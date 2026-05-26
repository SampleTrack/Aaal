"""
Feature 3a – Night Mode (premium).
During configured hours (UTC), all non-admin messages are silently deleted.
Default window: 22:00 – 06:00 UTC.
Command /setnighttime <start_hour> <end_hour> to customise.
"""
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from utils.admin_check import is_admin
from utils.error_logger import log_command


def _is_night(start: int, end: int) -> bool:
    hour = datetime.utcnow().hour
    if start > end:          # crosses midnight  e.g. 22 → 6
        return hour >= start or hour < end
    return start <= hour < end  # same-day window e.g. 2 → 5


@Client.on_message(filters.group & ~filters.service, group=3)
async def night_mode_filter(client: Client, message: Message):
    if not message.from_user:
        return

    chat_data = await db.get_chat(message.chat.id)
    if not chat_data.get("is_premium"):
        return

    prem = chat_data.get("premium_settings", {})
    if not prem.get("night_mode_enabled", False):
        return

    if not _is_night(prem.get("night_start", 22), prem.get("night_end", 6)):
        return

    if await is_admin(client, message):
        return

    try:
        await message.delete()
    except Exception:
        pass


@Client.on_message(filters.command("setnighttime") & filters.group)
@log_command
async def set_night_time(client: Client, message: Message):
    """Usage: /setnighttime 22 6  (start_hour end_hour, 24 h UTC)"""
    if not await is_admin(client, message):
        return await message.reply("⛔ Only admins can configure Night Mode.")

    chat_data = await db.get_chat(message.chat.id)
    if not chat_data.get("is_premium"):
        return await message.reply("🌟 Night Mode is a Premium feature. Use /upgrade.")

    args = message.text.split()
    if len(args) != 3:
        prem = chat_data.get("premium_settings", {})
        return await message.reply(
            f"⚙️ **Night Mode Hours** (UTC)\n"
            f"Current: `{prem.get('night_start', 22):02d}:00` → `{prem.get('night_end', 6):02d}:00`\n\n"
            f"Usage: `/setnighttime 22 6`"
        )

    try:
        start, end = int(args[1]), int(args[2])
        if not (0 <= start <= 23 and 0 <= end <= 23):
            raise ValueError
    except ValueError:
        return await message.reply("❌ Hours must be integers between 0 and 23.")

    await db.chats.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"premium_settings.night_start": start, "premium_settings.night_end": end}},
    )
    await message.reply(
        f"✅ Night Mode hours updated!\n"
        f"🌙 Active from **{start:02d}:00 UTC** to **{end:02d}:00 UTC**"
    )
