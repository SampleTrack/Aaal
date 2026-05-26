"""
Feature 4 – Anti-Forward filter (free).
Deletes forwarded messages from non-admins when enabled.
Bot itself and all admins/owners are exempt.
"""
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from utils.admin_check import is_admin
from utils.log_channel import send_group_log


@Client.on_message(filters.group & filters.forwarded & ~filters.service, group=2)
async def anti_forward_filter(client: Client, message: Message):
    if not message.from_user:
        return

    chat_data = await db.get_chat(message.chat.id)
    if not chat_data.get("free_settings", {}).get("anti_forward", False):
        return

    # Exempt admins and the bot itself
    if await is_admin(client, message):
        return

    try:
        await message.delete()
        # Log to group's premium log channel if set
        await send_group_log(
            client,
            message.chat.id,
            f"🚫 **Forwarded Message Deleted**\n"
            f"**User:** {message.from_user.mention}\n"
            f"**ID:** `{message.from_user.id}`",
        )
    except Exception:
        pass
