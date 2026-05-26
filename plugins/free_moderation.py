from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from utils.admin_check import is_admin
from utils.error_logger import log_command
from utils.log_channel import send_group_log
from database.db import db


async def _is_protected(client, chat_id: int, user_id: int) -> bool:
    """Return True if the target is an admin or owner (cannot be actioned)."""
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False


@Client.on_message(filters.command("ban") & filters.group)
@log_command
async def ban_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to ban them.")

    target = message.reply_to_message.from_user
    if await _is_protected(client, message.chat.id, target.id):
        return await message.reply("⛔ You cannot ban an admin or the group owner.")

    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await message.reply(f"🚫 {target.mention} has been banned.")
        await send_group_log(
            client, message.chat.id,
            f"🚫 **User Banned**\n"
            f"**User:** {target.mention} (`{target.id}`)\n"
            f"**By:** {message.from_user.mention}",
        )
    except Exception as e:
        await message.reply(f"❌ Failed to ban: {e}")


@Client.on_message(filters.command("mute") & filters.group)
@log_command
async def mute_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to mute them.")

    target = message.reply_to_message.from_user
    if await _is_protected(client, message.chat.id, target.id):
        return await message.reply("⛔ You cannot mute an admin or the group owner.")

    try:
        await client.restrict_chat_member(
            message.chat.id, target.id, ChatPermissions(can_send_messages=False)
        )
        await message.reply(f"🔇 {target.mention} has been muted.")
        await send_group_log(
            client, message.chat.id,
            f"🔇 **User Muted**\n"
            f"**User:** {target.mention} (`{target.id}`)\n"
            f"**By:** {message.from_user.mention}",
        )
    except Exception as e:
        await message.reply(f"❌ Failed to mute: {e}")


@Client.on_message(filters.command("kick") & filters.group)
@log_command
async def kick_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to kick them.")

    target = message.reply_to_message.from_user
    if await _is_protected(client, message.chat.id, target.id):
        return await message.reply("⛔ You cannot kick an admin or the group owner.")

    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await client.unban_chat_member(message.chat.id, target.id)
        await message.reply(f"👢 {target.mention} was kicked.")
        await send_group_log(
            client, message.chat.id,
            f"👢 **User Kicked**\n"
            f"**User:** {target.mention} (`{target.id}`)\n"
            f"**By:** {message.from_user.mention}",
        )
    except Exception as e:
        await message.reply(f"❌ Failed to kick: {e}")


@Client.on_message(filters.command("warn") & filters.group)
@log_command
async def warn_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to warn them.")

    target = message.reply_to_message.from_user
    if await _is_protected(client, message.chat.id, target.id):
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
            await send_group_log(
                client, chat_id,
                f"🚨 **Auto-Banned (Max Warns)**\n"
                f"**User:** {target.mention} (`{target.id}`)\n"
                f"**Warns:** {current_warns}/{max_warns}",
            )
        except Exception as e:
            await message.reply(f"❌ Could not ban after max warnings: {e}")
    else:
        await message.reply(f"⚠️ {target.mention} warned. ({current_warns}/{max_warns})")
        await send_group_log(
            client, chat_id,
            f"⚠️ **User Warned**\n"
            f"**User:** {target.mention} (`{target.id}`)\n"
            f"**Warns:** {current_warns}/{max_warns}\n"
            f"**By:** {message.from_user.mention}",
        )


@Client.on_message(filters.command("unwarn") & filters.group)
@log_command
async def unwarn_user(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("⛔ Only group admins can use this command.")
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a user's message to clear their warnings.")

    target = message.reply_to_message.from_user
    await db.reset_warns(message.chat.id, target.id)
    await message.reply(f"✅ All warnings cleared for {target.mention}.")
