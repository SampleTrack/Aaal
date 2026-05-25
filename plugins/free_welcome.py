from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db

@Client.on_message(filters.new_chat_members)
async def welcome_new_members(client: Client, message: Message):
    chat_data = await db.get_chat(message.chat.id)
    free_settings = chat_data.get("free_settings", {})

    # FIX: If premium captcha is active, skip the welcome message entirely.
    # premium_captcha.py already sends its own prompt — sending both is spammy and confusing.
    if (
        chat_data.get("is_premium")
        and chat_data.get("premium_settings", {}).get("captcha_enabled")
    ):
        return

    if not free_settings.get("welcome_enabled", True):
        return

    welcome_template = free_settings.get("welcome_text", "Welcome to the group!")

    for new_member in message.new_chat_members:
        if new_member.is_self:
            continue
        personalized_text = (
            welcome_template
            .replace("{mention}", new_member.mention)
            .replace("{title}", message.chat.title)
        )
        try:
            await message.reply(personalized_text)
        except Exception:
            pass
