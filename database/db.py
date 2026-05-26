from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config


class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["GroupManagerBot"]
        self.chats    = self.db["chats"]
        self.warnings = self.db["warnings"]
        self.captchas = self.db["captchas"]

    async def ensure_indexes(self):
        await self.chats.create_index("chat_id", unique=True)
        await self.warnings.create_index(
            [("chat_id", 1), ("user_id", 1)], unique=True
        )
        await self.captchas.create_index(
            [("chat_id", 1), ("user_id", 1)], unique=True
        )
        # Auto-delete captcha docs 120 s after creation
        await self.captchas.create_index("created_at", expireAfterSeconds=120)

    # ── Chat / settings ────────────────────────────────────────────────────

    async def get_chat(self, chat_id: int) -> Dict[str, Any]:
        chat = await self.chats.find_one({"chat_id": chat_id})
        if not chat:
            default = {
                "chat_id": chat_id,
                "is_premium": False,
                "premium_expires_at": None,
                "free_settings": {
                    "welcome_enabled": True,
                    "welcome_text":    "Welcome to the group!",
                    "anti_link":       False,
                    "anti_forward":    False,   # Feature 4
                    "max_warns":       3,
                },
                "premium_settings": {
                    "captcha_enabled":  False,
                    "night_mode_enabled": False, # Feature 3a
                    "night_start":      22,      # 10 PM UTC
                    "night_end":        6,       # 06 AM UTC
                    "log_channel_id":   None,    # Feature 3b
                },
            }
            await self.chats.insert_one(default)
            return default

        # Enforce premium expiry
        if (
            chat.get("is_premium")
            and chat.get("premium_expires_at")
            and chat["premium_expires_at"] < datetime.utcnow()
        ):
            await self.chats.update_one(
                {"chat_id": chat_id}, {"$set": {"is_premium": False}}
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
            {"$set": {"is_premium": True, "premium_expires_at": new_expiry}},
        )

    # ── Warnings ───────────────────────────────────────────────────────────

    async def add_warn(self, chat_id: int, user_id: int) -> int:
        doc = await self.warnings.find_one({"chat_id": chat_id, "user_id": user_id})
        if not doc:
            await self.warnings.insert_one(
                {"chat_id": chat_id, "user_id": user_id, "count": 1}
            )
            return 1
        new = doc["count"] + 1
        await self.warnings.update_one({"_id": doc["_id"]}, {"$set": {"count": new}})
        return new

    async def reset_warns(self, chat_id: int, user_id: int):
        await self.warnings.delete_one({"chat_id": chat_id, "user_id": user_id})

    # ── Captcha persistence ────────────────────────────────────────────────

    async def set_captcha(self, chat_id: int, user_id: int, answer: int, msg_id: int):
        await self.captchas.replace_one(
            {"chat_id": chat_id, "user_id": user_id},
            {
                "chat_id": chat_id, "user_id": user_id,
                "answer": answer, "msg_id": msg_id,
                "created_at": datetime.utcnow(),
            },
            upsert=True,
        )

    async def get_captcha(self, chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        return await self.captchas.find_one({"chat_id": chat_id, "user_id": user_id})

    async def delete_captcha(self, chat_id: int, user_id: int):
        await self.captchas.delete_one({"chat_id": chat_id, "user_id": user_id})

    # ── Premium: group log channel ─────────────────────────────────────────

    async def set_group_log_channel(self, chat_id: int, log_channel_id: Optional[int]):
        await self.chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"premium_settings.log_channel_id": log_channel_id}},
        )

    async def get_group_log_channel(self, chat_id: int) -> Optional[int]:
        chat = await self.get_chat(chat_id)
        return chat.get("premium_settings", {}).get("log_channel_id")


db = Database()
