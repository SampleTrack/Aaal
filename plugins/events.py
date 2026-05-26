"""
Feature 2 – LOG_CHANNEL events:
  • Bot added to a new group
  • Bot removed from a group
  • New premium subscription confirmed
"""
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.log_channel import send_log


@Client.on_message(filters.new_chat_members)
async def on_bot_added(client: Client, message: Message):
    """Fires when the bot itself is added to a group."""
    for member in message.new_chat_members:
        if not member.is_self:
            continue
        added_by = message.from_user.mention if message.from_user else "Unknown"
        await send_log(
            client,
            f"➕ **Bot Added to New Group**\n\n"
            f"**Group:** {message.chat.title}\n"
            f"**Group ID:** `{message.chat.id}`\n"
            f"**Added by:** {added_by}",
        )


@Client.on_message(filters.left_chat_member)
async def on_bot_removed(client: Client, message: Message):
    """Fires when the bot itself is removed from a group."""
    if not message.left_chat_member:
        return
    bot_info = await client.get_me()
    if message.left_chat_member.id != bot_info.id:
        return
    await send_log(
        client,
        f"➖ **Bot Removed from Group**\n\n"
        f"**Group:** {message.chat.title}\n"
        f"**Group ID:** `{message.chat.id}`",
    )
