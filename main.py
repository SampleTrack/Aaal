import os
import asyncio
import logging
from pyrogram import Client, idle
from aiohttp import web
from config import Config

logging.basicConfig(level=logging.INFO)

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
    await app.start()
    logging.info("Pyrogram Bot started successfully.")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
