from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["GroupManagerBot"]
        self.chats = self.db["chats"]
        self.warnings = self.db["warnings"]
        self.captchas = self.db["captchas"]  # FIX: persistent captcha store

    async def ensure_indexes(self):
        """
        SUGGESTION: Create indexes on startup so queries never do full collection scans.
        Call this once from main.py before the bot starts.
        """
        await self.chats.create_index("chat_id", unique=True)
        await self.warnings.create_index(
            [("chat_id", 1), ("user_id", 1)], unique=True
        )
        await self.captchas.create_index(
            [("chat_id", 1), ("user_id", 1)], unique=True
        )
        # Auto-delete captcha docs after 120s (TTL index) so stale docs never accumulate
        await self.captchas.create_index("created_at", expireAfterSeconds=120)

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

        # FIX: Enforce premium expiry — flip is_premium back to False if subscription lapsed
        if (
            chat.get("is_premium")
            and chat.get("premium_expires_at")
            and chat["premium_expires_at"] < datetime.utcnow()
        ):
            await self.chats.update_one(
                {"chat_id": chat_id},
                {"$set": {"is_premium": False}}
            )
            chat["is_premium"] = False

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

    # ------------------------------------------------------------------
    # FIX: Captcha persistence methods (replaces the in-memory dict)
    # ------------------------------------------------------------------

    async def set_captcha(self, chat_id: int, user_id: int, answer: int, msg_id: int):
        """Persist a pending captcha so it survives bot restarts."""
        await self.captchas.replace_one(
            {"chat_id": chat_id, "user_id": user_id},
            {
                "chat_id": chat_id,
                "user_id": user_id,
                "answer": answer,
                "msg_id": msg_id,
                "created_at": datetime.utcnow()
            },
            upsert=True
        )

    async def get_captcha(self, chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        return await self.captchas.find_one({"chat_id": chat_id, "user_id": user_id})

    async def delete_captcha(self, chat_id: int, user_id: int):
        await self.captchas.delete_one({"chat_id": chat_id, "user_id": user_id})


db = Database()
