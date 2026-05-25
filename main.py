import os
import asyncio
import logging

# FIX: Explicitly create and set the event loop BEFORE importing Pyrogram.
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, idle
from aiohttp import web
from config import Config
from database.db import db

logging.basicConfig(level=logging.INFO)

# FIX: Fail fast if OWNER_ID was never set — avoids silently opening owner commands
# to user ID 0 (Telegram service accounts).
if Config.OWNER_ID == 0:
    raise RuntimeError(
        "OWNER_ID environment variable is not set. "
        "Add your Telegram user ID to .env or Render's environment variables and redeploy."
    )

app = Client(
    "group_manager",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

async def health_check(request):
    return web.Response(text="Bot is perfectly running on Render!")

async def start_web_server():
    server = web.Application()
    server.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    await site.start()
    logging.info(f"Dummy web server started on port {Config.PORT}")

async def main():
    await start_web_server()

    # SUGGESTION: Create MongoDB indexes once at startup so all queries are fast
    await db.ensure_indexes()
    logging.info("MongoDB indexes verified.")

    await app.start()
    logging.info("Pyrogram Bot started successfully.")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
