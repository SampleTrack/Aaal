from pyrogram import Client, filters
from pyrogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import db
from config import Config
from utils.admin_check import is_admin

STAR_PRICE = [LabeledPrice(label="30 Days Premium", amount=Config.PREMIUM_PRICE_STARS)]

@Client.on_message(filters.command("upgrade") & filters.group)
async def send_upgrade_invoice(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    await client.send_invoice(
        chat_id=message.chat.id,
        title="Group Premium Upgrade",
        description="Unlock Captcha and Filters for 30 days.",
        payload=f"premium_upgrade_{message.chat.id}",
        provider_token="",
        currency="XTR",
        prices=STAR_PRICE,
        start_parameter="premium_upgrade"
    )

@Client.on_pre_checkout_query()
async def confirm_checkout(client: Client, query: PreCheckoutQuery):
    await client.answer_pre_checkout_query(query.id, ok=True)

@Client.on_message(filters.successful_payment)
async def handle_payment_success(client: Client, message: Message):
    payment = message.successful_payment
    if payment.invoice_payload == f"premium_upgrade_{message.chat.id}":
        await db.add_premium_time(message.chat.id, 30)
        await message.reply("Transaction confirmed. Premium unlocked for 30 days.")
