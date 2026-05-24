import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from utils.admin_check import is_admin

URL_PATTERN = re.compile(r"https?://[^\s]+")

@Client.on_message(filters.group & ~filters.service, group=1)
async def link_deletion_filter(client: Client, message: Message):
    if not message.from_user or await is_admin(client, message):
        return

    chat_data = await db.get_chat(message.chat.id)
    if not chat_data.get("free_settings", {}).get("anti_link", False):
        return

    text_to_scan = message.text or message.caption or ""
    if URL_PATTERN.search(text_to_scan):
        try:
            await message.delete()
        except Exception:
            pass
