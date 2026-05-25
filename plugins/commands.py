from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    if message.chat.type.value == "private":
        bot_info = await client.get_me()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add to your Group", url=f"https://t.me/{bot_info.username}?startgroup=true")],
            [InlineKeyboardButton("📚 Help", callback_data="help_menu")]
        ])
        await message.reply(
            f"Hello, {message.from_user.mention}! 👋\n\n"
            "I am a high-performance Group Manager Bot.\n"
            "Add me to your group and promote me to admin to unlock moderation tools, anti-spam filters, and premium features.",
            reply_markup=keyboard
        )
    else:
        await message.reply("🛡️ Bot is online, active, and monitoring this group!")

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    help_text = (
        "**📚 Bot Command Guide**\n\n"
        "**Free Moderation:**\n"
        "• `/ban` [reply] - Permanently removes a user.\n"
        "• `/kick` [reply] - Removes a user (they can rejoin).\n"
        "• `/mute` [reply] - Silences a user indefinitely.\n"
        "• `/warn` [reply] - Adds a warning (bans at 3 warnings).\n"
        "• `/unwarn` [reply] - Clears all warnings for a user.\n\n"
        "**Premium Features:**\n"
        "• `/upgrade` - Unlock Captchas and Advanced Filters for 30 days via Telegram Stars.\n\n"
        "**General:**\n"
        "• `/start` - Check if the bot is alive.\n"
        "• `/about` - View bot information."
    )
    await message.reply(help_text)

@Client.on_message(filters.command("about"))
async def about_command(client: Client, message: Message):
    about_text = (
        "**🤖 About Group Manager Bot**\n\n"
        "I am a robust, high-speed Telegram group management assistant built to keep your communities safe and spam-free.\n\n"
        "**Version:** 1.1.0\n"
        "**Engine:** Pyrogram & MongoDB\n"
        "**Hosting:** Render\n\n"
        "Thank you for trusting me to protect your group!"
    )
    await message.reply(about_text)

@Client.on_callback_query(filters.regex("^help_menu$"))
async def help_callback(client: Client, callback_query):
    help_text = (
        "**📚 Bot Command Guide**\n\n"
        "**Free Moderation:**\n"
        "• `/ban` [reply] - Permanently removes a user.\n"
        "• `/kick` [reply] - Removes a user (they can rejoin).\n"
        "• `/mute` [reply] - Silences a user indefinitely.\n"
        "• `/warn` [reply] - Adds a warning (bans at 3 warnings).\n"
        "• `/unwarn` [reply] - Clears all warnings for a user.\n\n"
        "**Premium Features:**\n"
        "• `/upgrade` - Unlock Captchas and Advanced Filters for 30 days via Telegram Stars."
    )
    await callback_query.message.edit_text(help_text)
