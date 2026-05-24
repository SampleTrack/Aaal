from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from utils.admin_check import is_admin
from database.db import db

@Client.on_message(filters.command("ban") & filters.group)
async def ban_user(client: Client, message: Message):
    if not await is_admin(client, message) or not message.reply_to_message:
        return
    target = message.reply_to_message.from_user
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await message.reply(f"{target.mention} has been banned.")
    except Exception:
        pass

@Client.on_message(filters.command("mute") & filters.group)
async def mute_user(client: Client, message: Message):
    if not await is_admin(client, message) or not message.reply_to_message:
        return
    target = message.reply_to_message.from_user
    try:
        await client.restrict_chat_member(message.chat.id, target.id, ChatPermissions(can_send_messages=False))
        await message.reply(f"{target.mention} has been muted.")
    except Exception:
        pass

@Client.on_message(filters.command("kick") & filters.group)
async def kick_user(client: Client, message: Message):
    if not await is_admin(client, message) or not message.reply_to_message:
        return
    target = message.reply_to_message.from_user
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await client.unban_chat_member(message.chat.id, target.id)
        await message.reply(f"{target.mention} was kicked.")
    except Exception:
        pass

@Client.on_message(filters.command("warn") & filters.group)
async def warn_user(client: Client, message: Message):
    if not await is_admin(client, message) or not message.reply_to_message:
        return
        
    target = message.reply_to_message.from_user
    chat_id = message.chat.id
    chat_data = await db.get_chat(chat_id)
    max_warns = chat_data["free_settings"].get("max_warns", 3)
    
    current_warns = await db.add_warn(chat_id, target.id)
    
    if current_warns >= max_warns:
        try:
            await client.ban_chat_member(chat_id, target.id)
            await message.reply(f"🚨 {target.mention} reached {max_warns} warnings and was banned!")
            await db.reset_warns(chat_id, target.id) 
        except Exception:
            pass
    else:
        await message.reply(f"⚠️ {target.mention} warned. ({current_warns}/{max_warns})")
