from datetime import datetime, timedelta
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["GroupManagerBot"]
        self.chats = self.db["chats"]
        self.warnings = self.db["warnings"]

    async def get_chat(self, chat_id: int) -> Dict[str, Any]:
        chat = await self.chats.find_one({"chat_id": chat_id})
        if not chat:
            default_schema = {
                "chat_id": chat_id,
                "is_premium": False,
                "premium_expires_at": None,
                "free_settings": {
                    "welcome_enabled": True,
                    "welcome_text": "Welcome to the group!",
                    "anti_link": False,
                    "max_warns": 3
                },
                "premium_settings": {
                    "captcha_enabled": False
                }
            }
            await self.chats.insert_one(default_schema)
            return default_schema
        return chat

    async def add_premium_time(self, chat_id: int, days: int = 30):
        chat = await self.get_chat(chat_id)
        if chat.get("is_premium") and chat.get("premium_expires_at"):
            new_expiry = chat["premium_expires_at"] + timedelta(days=days)
        else:
            new_expiry = datetime.utcnow() + timedelta(days=days)
            
        await self.chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"is_premium": True, "premium_expires_at": new_expiry}}
        )

    async def add_warn(self, chat_id: int, user_id: int) -> int:
        warn_doc = await self.warnings.find_one({"chat_id": chat_id, "user_id": user_id})
        if not warn_doc:
            await self.warnings.insert_one({"chat_id": chat_id, "user_id": user_id, "count": 1})
            return 1
        else:
            new_count = warn_doc["count"] + 1
            await self.warnings.update_one({"_id": warn_doc["_id"]}, {"$set": {"count": new_count}})
            return new_count

    async def reset_warns(self, chat_id: int, user_id: int):
        await self.warnings.delete_one({"chat_id": chat_id, "user_id": user_id})

db = Database()
