from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    if message.chat.type.value == "private":
        bot_info = await client.get_me()
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_info.username}?startgroup=true")],
            [InlineKeyboardButton("📚 Help", callback_data="help_menu")],
        ])
        await message.reply(
            f"Hello, {message.from_user.mention}! 👋\n\n"
            "I am a high-performance Group Manager Bot.\n"
            "Add me to your group and make me admin to get started.",
            reply_markup=keyboard,
        )
    else:
        await message.reply("🛡️ Bot is online and monitoring this group!")

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    await message.reply(_help_text())

@Client.on_callback_query(filters.regex("^help_menu$"))
async def help_callback(client, cq):
    await cq.message.edit_text(_help_text())

@Client.on_message(filters.command("about"))
async def about_command(client: Client, message: Message):
    await message.reply(
        "**🤖 About Group Manager Bot**\n\n"
        "A robust, high-speed group management assistant.\n\n"
        "**Version:** 2.0.0\n"
        "**Engine:** Pyrogram & MongoDB\n"
        "**Hosting:** Render"
    )

def _help_text() -> str:
    return (
        "**📚 Command Guide**\n\n"
        "**Free Moderation:**\n"
        "• `/ban` — Permanently ban a user.\n"
        "• `/kick` — Remove a user (can rejoin).\n"
        "• `/mute` — Silence a user.\n"
        "• `/warn` — Warn a user (auto-ban at limit).\n"
        "• `/unwarn` — Clear a user's warnings.\n"
        "• `/settings` — Toggle group features.\n\n"
        "**Premium Features:**\n"
        "• `/upgrade` — Unlock premium (30 days via Stars).\n"
        "• `/setnighttime HH HH` — Configure Night Mode hours.\n"
        "• `/setlogchannel ID` — Set group log channel.\n"
        "• `/removelogchannel` — Remove log channel.\n\n"
        "**General:**\n"
        "• `/start` — Check bot status.\n"
        "• `/about` — Bot info."
    )
