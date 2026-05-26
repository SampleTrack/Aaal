"""
Feature 3b – Admin Personal Log Channel (premium).
Group admins can route all moderation events to their own Telegram channel.
"""
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from utils.admin_check import is_admin
from utils.error_logger import log_command


@Client.on_message(filters.command("setlogchannel") & filters.group)
@log_command
async def set_log_channel(client: Client, message: Message):
    """Usage: /setlogchannel -100xxxxxxxxxx"""
    if not await is_admin(client, message):
        return await message.reply("⛔ Only admins can set a log channel.")

    chat_data = await db.get_chat(message.chat.id)
    if not chat_data.get("is_premium"):
        return await message.reply("🌟 Admin Log Channel is a Premium feature. Use /upgrade.")

    args = message.text.split()
    if len(args) < 2:
        current = chat_data.get("premium_settings", {}).get("log_channel_id")
        status = f"`{current}`" if current else "Not configured."
        return await message.reply(
            f"📋 **Group Log Channel**\n\n"
            f"**Current:** {status}\n\n"
            f"**Usage:** `/setlogchannel -100xxxxxxxxxx`\n"
            f"_(Make sure the bot is an admin in that channel first.)_"
        )

    try:
        log_channel_id = int(args[1])
    except ValueError:
        return await message.reply("❌ Invalid ID. Format: `/setlogchannel -100xxxxxxxxxx`")

    try:
        await client.send_message(
            log_channel_id,
            f"✅ **Log channel connected!**\n\n"
            f"All moderation events for **{message.chat.title}** will now appear here.",
        )
        await db.set_group_log_channel(message.chat.id, log_channel_id)
        await message.reply("✅ Log channel set! Moderation events will be sent there.")
    except Exception as e:
        await message.reply(
            f"❌ Could not reach that channel.\n"
            f"Make sure the bot is an admin there.\n\n`{e}`"
        )


@Client.on_message(filters.command("removelogchannel") & filters.group)
@log_command
async def remove_log_channel(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only admins can manage the log channel.")
    await db.set_group_log_channel(message.chat.id, None)
    await message.reply("✅ Log channel removed.")
