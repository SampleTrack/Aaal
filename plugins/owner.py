import asyncio, os
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from config import Config
from utils.log_channel import send_log
from utils.error_logger import log_command

def is_owner(_, __, m: Message):
    return bool(m.from_user and m.from_user.id == Config.OWNER_ID)

owner_filter = filters.create(is_owner)

@Client.on_message(filters.command("stats") & owner_filter)
@log_command
async def bot_stats(client: Client, message: Message):
    msg = await message.reply("📊 Fetching stats...")
    try:
        total   = await db.chats.count_documents({})
        premium = await db.chats.count_documents({"is_premium": True})
        warns   = await db.warnings.count_documents({})
        await msg.edit_text(
            f"**📈 Dashboard**\n\n"
            f"**Total Groups:** {total}\n"
            f"**Premium:** {premium}\n"
            f"**Total Warns:** {warns}\n\n"
            f"Systems nominal. 🟢"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

@Client.on_message(filters.command("logs") & owner_filter)
@log_command
async def get_logs(client: Client, message: Message):
    """Send the two log files as documents."""
    files = {"logs/bot_errors.log": "🔴 Error Log", "logs/commands.log": "📋 Commands Log"}
    sent = False
    for path, label in files.items():
        if os.path.exists(path) and os.path.getsize(path) > 0:
            await client.send_document(
                message.chat.id, path,
                caption=label, reply_to_message_id=message.id,
            )
            sent = True
    if not sent:
        await message.reply("📭 Log files are empty or not created yet.")

@Client.on_message(filters.command("clearlogs") & owner_filter)
@log_command
async def clear_logs(client: Client, message: Message):
    """Wipe both log files."""
    for path in ("logs/bot_errors.log", "logs/commands.log"):
        if os.path.exists(path):
            open(path, "w").close()
    await message.reply("🗑️ Log files cleared.")

@Client.on_message(filters.command("forceupgrade") & owner_filter)
@log_command
async def force_upgrade(client: Client, message: Message):
    args = message.text.split()
    if len(args) != 3:
        return await message.reply("⚠️ Usage: `/forceupgrade -100123456789 30`")
    try:
        target_chat_id, days = int(args[1]), int(args[2])
        await db.add_premium_time(target_chat_id, days)
        await message.reply(f"✅ Group `{target_chat_id}` granted {days} days of Premium.")
        await send_log(
            client,
            f"🌟 **Premium Granted (Manual)**\n"
            f"**Group:** `{target_chat_id}`\n**Days:** {days}\n"
            f"**By:** {message.from_user.mention}",
        )
        try:
            await client.send_message(
                target_chat_id,
                f"🎉 The developer has granted this group **{days} days** of Premium!",
            )
        except Exception:
            pass
    except ValueError:
        await message.reply("❌ Chat ID and Days must be numbers.")

@Client.on_message(filters.command("broadcast") & owner_filter)
@log_command
async def broadcast_message(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply("⚠️ Usage: `/broadcast Hello!` or reply to a message.")
    text = (message.text.split(None, 1)[1] if len(message.command) > 1
            else message.reply_to_message.text)
    msg = await message.reply("📡 Broadcasting...")
    ok = fail = 0
    async for chat in db.chats.find({}):
        try:
            await client.send_message(chat["chat_id"], f"📢 **Broadcast:**\n\n{text}")
            ok += 1
            await asyncio.sleep(0.1)
        except Exception:
            fail += 1
    await msg.edit_text(f"✅ Done!\n**Sent:** {ok}\n**Failed:** {fail}")
