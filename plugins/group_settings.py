from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from database.db import db
from utils.admin_check import is_admin

def get_settings_keyboard(chat_data: dict) -> InlineKeyboardMarkup:
    free  = chat_data.get("free_settings", {})
    prem  = chat_data.get("premium_settings", {})
    is_p  = chat_data.get("is_premium", False)
    lock  = "" if is_p else " 🔒"

    def s(val): return "🟢 ON" if val else "🔴 OFF"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Welcome Message: {s(free.get('welcome_enabled', True))}",   callback_data="toggle_welcome")],
        [InlineKeyboardButton(f"Anti-Link Filter: {s(free.get('anti_link', False))}",        callback_data="toggle_antilink")],
        [InlineKeyboardButton(f"Anti-Forward: {s(free.get('anti_forward', False))}",         callback_data="toggle_antiforward")],
        [InlineKeyboardButton(f"Math Captcha (Premium): {s(prem.get('captcha_enabled', False))}{lock}",    callback_data="toggle_captcha")],
        [InlineKeyboardButton(f"Night Mode (Premium): {s(prem.get('night_mode_enabled', False))}{lock}",   callback_data="toggle_nightmode")],
    ])

@Client.on_message(filters.command("settings") & filters.group)
async def open_settings(client: Client, message: Message):
    if not await is_admin(client, message):
        return
    chat_data = await db.get_chat(message.chat.id)
    await message.reply(
        "⚙️ **Group Control Panel**\n\nToggle features ON or OFF. Admins only.",
        reply_markup=get_settings_keyboard(chat_data),
    )

@Client.on_callback_query(filters.regex(r"^toggle_"))
async def handle_toggle(client: Client, query: CallbackQuery):
    chat_id = query.message.chat.id
    try:
        m = await client.get_chat_member(chat_id, query.from_user.id)
        if m.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await query.answer("⛔ Admins only.", show_alert=True)
    except Exception:
        return await query.answer("Error verifying admin status.", show_alert=True)

    chat_data = await db.get_chat(chat_id)
    action = query.data[len("toggle_"):]   # everything after "toggle_"

    if action == "welcome":
        cur = chat_data["free_settings"].get("welcome_enabled", True)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"free_settings.welcome_enabled": not cur}})

    elif action == "antilink":
        cur = chat_data["free_settings"].get("anti_link", False)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"free_settings.anti_link": not cur}})

    elif action == "antiforward":
        cur = chat_data["free_settings"].get("anti_forward", False)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"free_settings.anti_forward": not cur}})

    elif action == "captcha":
        if not chat_data.get("is_premium"):
            return await query.answer("🌟 Requires Premium. Use /upgrade.", show_alert=True)
        cur = chat_data["premium_settings"].get("captcha_enabled", False)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"premium_settings.captcha_enabled": not cur}})

    elif action == "nightmode":
        if not chat_data.get("is_premium"):
            return await query.answer("🌟 Requires Premium. Use /upgrade.", show_alert=True)
        cur = chat_data["premium_settings"].get("night_mode_enabled", False)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"premium_settings.night_mode_enabled": not cur}})

    updated = await db.get_chat(chat_id)
    await query.message.edit_reply_markup(reply_markup=get_settings_keyboard(updated))
    await query.answer("Updated!")
