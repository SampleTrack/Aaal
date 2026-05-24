import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from config import Config

# --- 1. THE SECURITY GATEKEEPER ---
# This custom filter ensures ONLY the ID listed in Config.OWNER_ID can run these commands.
def is_owner(_, __, message: Message):
    return bool(message.from_user and message.from_user.id == Config.OWNER_ID)

owner_filter = filters.create(is_owner)


# --- 2. THE STATS COMMAND ---
@Client.on_message(filters.command("stats") & owner_filter)
async def bot_stats(client: Client, message: Message):
    """
    Pulls real-time analytics from MongoDB.
    """
    processing_msg = await message.reply("📊 Fetching live statistics from database...")
    
    try:
        # Count documents directly from our MongoDB collections
        total_groups = await db.chats.count_documents({})
        premium_groups = await db.chats.count_documents({"is_premium": True})
        total_warns = await db.warnings.count_documents({})
        
        stats_text = (
            "**📈 Group Manager Dashboard**\n\n"
            f"**Total Groups:** {total_groups}\n"
            f"**Premium Subscriptions:** {premium_groups}\n"
            f"**Total Warnings Issued:** {total_warns}\n\n"
            "Systems are running nominally. 🟢"
        )
        await processing_msg.edit_text(stats_text)
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error fetching stats: {e}")


# --- 3. THE FORCE UPGRADE COMMAND ---
@Client.on_message(filters.command("forceupgrade") & owner_filter)
async def force_upgrade(client: Client, message: Message):
    """
    Usage: /forceupgrade <chat_id> <days>
    Manually bypasses the payment gateway and assigns premium status.
    """
    # Check if the owner provided the right arguments
    args = message.text.split()
    if len(args) != 3:
        await message.reply("⚠️ **Syntax Error:** Use `/forceupgrade -100123456789 30`")
        return
        
    try:
        target_chat_id = int(args[1])
        days = int(args[2])
        
        # We reuse the exact same database function the payment gateway uses!
        await db.add_premium_time(target_chat_id, days)
        await message.reply(f"✅ **Success!** Group `{target_chat_id}` has been granted {days} days of Premium.")
        
        # Notify the target group if the bot is still inside it
        try:
            await client.send_message(
                target_chat_id, 
                f"🎉 **Good news!** The developer has manually granted this group **{days} days** of Premium features!"
            )
        except Exception:
            # Fails silently if the bot was kicked from that group
            pass
            
    except ValueError:
        await message.reply("❌ **Error:** Chat ID and Days must be valid numbers.")


# --- 4. THE BROADCAST COMMAND ---
@Client.on_message(filters.command("broadcast") & owner_filter)
async def broadcast_message(client: Client, message: Message):
    """
    Usage: /broadcast <your message>
    Sends a message to every single group registered in the database.
    """
    # Ensure there is a message to send
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply("⚠️ **Syntax Error:** Use `/broadcast Hello everyone!` or reply to a message with `/broadcast`.")
        return

    # Extract the broadcast text
    broadcast_text = message.text.split(None, 1)[1] if len(message.command) > 1 else message.reply_to_message.text
    
    processing_msg = await message.reply("📡 Starting broadcast... this may take a while depending on group count.")
    
    success_count = 0
    failed_count = 0
    
    # Fetch all chats from the database cursor
    cursor = db.chats.find({})
    chats = await cursor.to_list(length=None)
    
    for chat in chats:
        try:
            await client.send_message(chat["chat_id"], f"📢 **Developer Broadcast:**\n\n{broadcast_text}")
            success_count += 1
            
            # CRITICAL: We must sleep to avoid Telegram's strict flood limits (max 30 msgs/second)
            await asyncio.sleep(0.1) 
        except Exception:
            # Group might have kicked the bot, or chat ID changed
            failed_count += 1
            
    await processing_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"**Successfully Sent:** {success_count} groups\n"
        f"**Failed (Bot Kicked):** {failed_count} groups"
    )

