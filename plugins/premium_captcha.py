import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from database.db import db


async def _kick_if_unverified(client: Client, chat_id: int, user_id: int, msg_id: int, delay: int = 60):
    """
    FIX: Runs as a detached task via asyncio.create_task() instead of blocking the
    handler with asyncio.sleep(60). This means:
    - The handler returns immediately, freeing up the event loop.
    - Many users joining at once no longer pile up sleeping coroutines.
    - Bot restart risk is reduced (the DB record is the source of truth, not this task).
    """
    await asyncio.sleep(delay)

    # Check DB — if the record is gone, the user already solved it
    record = await db.get_captcha(chat_id, user_id)
    if record:
        await db.delete_captcha(chat_id, user_id)
        try:
            # Kick and unban = soft kick (they can rejoin but must re-solve on next entry)
            await client.ban_chat_member(chat_id, user_id)
            await client.unban_chat_member(chat_id, user_id)
            await client.delete_messages(chat_id, msg_id)
        except Exception:
            pass


@Client.on_message(filters.new_chat_members)
async def enforce_captcha(client: Client, message: Message):
    chat_data = await db.get_chat(message.chat.id)
    if not chat_data.get("is_premium") or not chat_data["premium_settings"].get("captcha_enabled"):
        return

    for new_member in message.new_chat_members:
        if new_member.is_self:
            continue

        await client.restrict_chat_member(
            message.chat.id, new_member.id, ChatPermissions(can_send_messages=False)
        )

        num1, num2 = random.randint(1, 10), random.randint(1, 10)
        correct_answer = num1 + num2

        # Build 3 shuffled answer buttons (correct + two wrong)
        wrong = list({correct_answer + 1, correct_answer - 1, correct_answer + 2} - {correct_answer})[:2]
        answers = [correct_answer] + wrong
        random.shuffle(answers)
        buttons = [
            InlineKeyboardButton(str(a), callback_data=f"captcha_{new_member.id}_{a}")
            for a in answers
        ]

        captcha_msg = await message.reply(
            f"🚨 {new_member.mention}, human verification required.\n"
            f"What is **{num1} + {num2}**? You have 60 seconds.",
            reply_markup=InlineKeyboardMarkup([buttons])
        )

        # FIX: Persist to MongoDB so state survives a bot restart
        await db.set_captcha(message.chat.id, new_member.id, correct_answer, captcha_msg.id)

        # FIX: Detach the timeout — handler returns immediately
        asyncio.create_task(
            _kick_if_unverified(client, message.chat.id, new_member.id, captcha_msg.id)
        )


@Client.on_callback_query(filters.regex(r"^captcha_"))
async def verify_captcha_click(client, callback_query):
    parts = callback_query.data.split("_")
    target_user_id = int(parts[1])
    clicked_answer = int(parts[2])
    chat_id = callback_query.message.chat.id
    clicker_id = callback_query.from_user.id

    if clicker_id != target_user_id:
        return await callback_query.answer("This captcha isn't for you.", show_alert=True)

    # FIX: Read from DB instead of the in-memory dict
    record = await db.get_captcha(chat_id, clicker_id)
    if not record:
        return await callback_query.answer("Captcha expired or already completed.", show_alert=True)

    await db.delete_captcha(chat_id, clicker_id)

    if clicked_answer == record["answer"]:
        await client.restrict_chat_member(
            chat_id, clicker_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await callback_query.message.delete()
        await callback_query.answer("✅ Verified! Welcome to the group.", show_alert=True)
    else:
        await callback_query.message.delete()
        await client.ban_chat_member(chat_id, clicker_id)
        await client.unban_chat_member(chat_id, clicker_id)
        await callback_query.answer("❌ Wrong answer. You've been removed.", show_alert=True)
