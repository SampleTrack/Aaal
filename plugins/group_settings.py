from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from database.db import db
from utils.admin_check import is_admin

def get_settings_keyboard(chat_data: dict) -> InlineKeyboardMarkup:
    """
    Helper function to dynamically build the settings keyboard based on current database state.
    """
    free = chat_data.get("free_settings", {})
    prem = chat_data.get("premium_settings", {})
    is_prem = chat_data.get("is_premium", False)

    # Determine button text based on boolean state
    welcome_status = "🟢 ON" if free.get("welcome_enabled", True) else "🔴 OFF"
    antilink_status = "🟢 ON" if free.get("anti_link", False) else "🔴 OFF"
    captcha_status = "🟢 ON" if prem.get("captcha_enabled", False) else "🔴 OFF"
    
    # Add a lock emoji if the group is not premium
    prem_lock = "" if is_prem else " 🔒"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Welcome Message: {welcome_status}", callback_data="toggle_welcome")],
        [InlineKeyboardButton(f"Anti-Link Filter: {antilink_status}", callback_data="toggle_antilink")],
        [InlineKeyboardButton(f"Math Captcha (Premium): {captcha_status}{prem_lock}", callback_data="toggle_captcha")]
    ])
    return keyboard

@Client.on_message(filters.command("settings") & filters.group)
async def open_settings(client: Client, message: Message):
    """
    Renders the group control panel for admins.
    """
    if not await is_admin(client, message):
        return
        
    chat_data = await db.get_chat(message.chat.id)
    keyboard = get_settings_keyboard(chat_data)
    
    await message.reply(
        "⚙️ **Group Control Panel**\n\nClick the buttons below to toggle features ON or OFF. Only admins can use this menu.",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex(r"^toggle_"))
async def handle_toggle_click(client: Client, query: CallbackQuery):
    """
    Intercepts button clicks, verifies admin status, and updates MongoDB.
    """
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    
    # 1. Verify the person clicking is an Admin or Owner
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await query.answer("⛔ Access Denied: Only group admins can change settings.", show_alert=True)
    except Exception:
        return await query.answer("Error verifying your admin status.", show_alert=True)

    # 2. Fetch the current data to see what needs to be changed
    chat_data = await db.get_chat(chat_id)
    action = query.data.split("_")[1] # Extracts "welcome", "antilink", or "captcha"
    
    # 3. Process the specific toggle logic
    if action == "welcome":
        current_state = chat_data["free_settings"].get("welcome_enabled", True)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"free_settings.welcome_enabled": not current_state}})
        
    elif action == "antilink":
        current_state = chat_data["free_settings"].get("anti_link", False)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"free_settings.anti_link": not current_state}})
        
    elif action == "captcha":
        # Block the toggle entirely if they haven't paid for premium!
        if not chat_data.get("is_premium", False):
            return await query.answer("🌟 This feature requires a Premium upgrade! Type /upgrade to unlock it.", show_alert=True)
            
        current_state = chat_data["premium_settings"].get("captcha_enabled", False)
        await db.chats.update_one({"chat_id": chat_id}, {"$set": {"premium_settings.captcha_enabled": not current_state}})

    # 4. Fetch the newly updated data and refresh the buttons on the screen
    updated_chat_data = await db.get_chat(chat_id)
    new_keyboard = get_settings_keyboard(updated_chat_data)
    
    await query.message.edit_reply_markup(reply_markup=new_keyboard)
    await query.answer("Setting successfully updated!")
