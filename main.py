import os
import asyncio
import logging

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, idle
from aiohttp import web
from config import Config
from database.db import db
from utils.log_channel import send_log

logging.basicConfig(level=logging.INFO)

if Config.OWNER_ID == 0:
    raise RuntimeError(
        "OWNER_ID is not set. Add your Telegram user ID to the environment variables."
    )

app = Client(
    "group_manager",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins"),
)


async def health_check(request):
    return web.Response(text="Bot is perfectly running on Render!")


async def start_web_server():
    server = web.Application()
    server.add_routes([web.get("/", health_check)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
    logging.info(f"Web server started on port {Config.PORT}")


async def main():
    await start_web_server()
    await db.ensure_indexes()
    logging.info("MongoDB indexes verified.")

    await app.start()
    bot_info = await app.get_me()
    logging.info(f"Bot @{bot_info.username} started.")

    # Feature 2: notify owner LOG_CHANNEL that the bot came online
    await send_log(
        app,
        f"🟢 **Bot Online**\n\n"
        f"**Username:** @{bot_info.username}\n"
        f"**ID:** `{bot_info.id}`\n"
        f"**Time:** {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
    )

    await idle()
    await app.stop()


if __name__ == "__main__":
    loop.run_until_complete(main())
