import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    PORT = int(os.getenv("PORT", "8080"))
    PREMIUM_PRICE_STARS = int(os.getenv("PREMIUM_PRICE_STARS", "250"))
