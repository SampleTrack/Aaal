from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from utils.admin_check import is_admin
from database.db import db


# SUGGESTION: Helper to verify the target is not an admin/owner.
# Prevents one admin from banning another, matching standard bot behaviour.
async def is_target_protected(client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False


@Client.on_message(filters.command("ban") & filters.group)
async def ban_user(client: Client, message: Message):
    # FIX: Give clear feedback instead of silently doing nothing
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to ban them.")

    target = message.reply_to_message.from_user

    # SUGGESTION: Protect admins from being actioned by other admins
    if await is_target_protected(client, message.chat.id, target.id):
        return await message.reply("⛔ You cannot ban an admin or the group owner.")

    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await message.reply(f"🚫 {target.mention} has been banned.")
    except Exception as e:
        await message.reply(f"❌ Failed to ban: {e}")


@Client.on_message(filters.command("mute") & filters.group)
async def mute_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to mute them.")

    target = message.reply_to_message.from_user

    if await is_target_protected(client, message.chat.id, target.id):
        return await message.reply("⛔ You cannot mute an admin or the group owner.")

    try:
        await client.restrict_chat_member(
            message.chat.id, target.id, ChatPermissions(can_send_messages=False)
        )
        await message.reply(f"🔇 {target.mention} has been muted.")
    except Exception as e:
        await message.reply(f"❌ Failed to mute: {e}")


@Client.on_message(filters.command("kick") & filters.group)
async def kick_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to kick them.")

    target = message.reply_to_message.from_user

    if await is_target_protected(client, message.chat.id, target.id):
        return await message.reply("⛔ You cannot kick an admin or the group owner.")

    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await client.unban_chat_member(message.chat.id, target.id)
        await message.reply(f"👢 {target.mention} was kicked.")
    except Exception as e:
        await message.reply(f"❌ Failed to kick: {e}")


@Client.on_message(filters.command("warn") & filters.group)
async def warn_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to warn them.")

    target = message.reply_to_message.from_user

    if await is_target_protected(client, message.chat.id, target.id):
        return await message.reply("⛔ You cannot warn an admin or the group owner.")

    chat_id = message.chat.id
    chat_data = await db.get_chat(chat_id)
    max_warns = chat_data["free_settings"].get("max_warns", 3)

    current_warns = await db.add_warn(chat_id, target.id)

    if current_warns >= max_warns:
        try:
            await client.ban_chat_member(chat_id, target.id)
            await message.reply(f"🚨 {target.mention} reached {max_warns} warnings and was banned!")
            await db.reset_warns(chat_id, target.id)
        except Exception as e:
            await message.reply(f"❌ Could not ban after max warnings: {e}")
    else:
        await message.reply(f"⚠️ {target.mention} warned. ({current_warns}/{max_warns})")


# SUGGESTION: /unwarn command — the reset_warns DB function already existed,
# it just had no handler. Admins need a way to correct false warnings.
@Client.on_message(filters.command("unwarn") & filters.group)
async def unwarn_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to remove their warnings.")

    target = message.reply_to_message.from_user
    await db.reset_warns(message.chat.id, target.id)
    await message.reply(f"✅ All warnings cleared for {target.mention}.")
