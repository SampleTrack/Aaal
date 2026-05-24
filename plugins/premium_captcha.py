import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from database.db import db

pending_captchas = {}

@Client.on_message(filters.new_chat_members)
async def enforce_captcha(client: Client, message: Message):
    chat_data = await db.get_chat(message.chat.id)
    if not chat_data.get("is_premium", False) or not chat_data["premium_settings"].get("captcha_enabled", False):
        return

    for new_member in message.new_chat_members:
        if new_member.is_self:
            continue

        await client.restrict_chat_member(message.chat.id, new_member.id, ChatPermissions(can_send_messages=False))
        
        num1, num2 = random.randint(1, 10), random.randint(1, 10)
        correct_answer = num1 + num2
        pending_captchas[f"{message.chat.id}_{new_member.id}"] = correct_answer

        answers = [correct_answer, correct_answer + 1, correct_answer - random.randint(1, 3)]
        random.shuffle(answers)
        buttons = [InlineKeyboardButton(str(ans), callback_data=f"captcha_{new_member.id}_{ans}") for ans in answers]

        captcha_msg = await message.reply(
            f"🚨 {new_member.mention}, human verification. What is **{num1} + {num2}**?",
            reply_markup=InlineKeyboardMarkup([buttons])
        )

        await asyncio.sleep(60)
        
        if f"{message.chat.id}_{new_member.id}" in pending_captchas:
            del pending_captchas[f"{message.chat.id}_{new_member.id}"]
            try:
                await client.ban_chat_member(message.chat.id, new_member.id)
                await client.unban_chat_member(message.chat.id, new_member.id)
                await captcha_msg.delete()
            except Exception:
                pass

@Client.on_callback_query(filters.regex(r"^captcha_"))
async def verify_captcha_click(client: Client, callback_query):
    data = callback_query.data.split("_")
    target_user_id, clicked_answer = int(data[1]), int(data[2])
    chat_id, clicker_id = callback_query.message.chat.id, callback_query.from_user.id

    if clicker_id != target_user_id:
        return await callback_query.answer("Access denied.", show_alert=True)

    key = f"{chat_id}_{clicker_id}"
    if key not in pending_captchas:
        return await callback_query.answer("Captcha expired.", show_alert=True)

    if clicked_answer == pending_captchas[key]:
        del pending_captchas[key]
        await client.restrict_chat_member(
            chat_id, clicker_id,
            ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        )
        await callback_query.message.delete()
        await callback_query.answer("Passed.", show_alert=True)
    else:
        del pending_captchas[key]
        await callback_query.message.delete()
        await client.ban_chat_member(chat_id, clicker_id)
        await client.unban_chat_member(chat_id, clicker_id)
        await callback_query.answer("Failed. Ejecting.", show_alert=True)
