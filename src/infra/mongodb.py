from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from core.logger import logger

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(settings.MONGO_URI)
            cls.db = cls.client[settings.MONGO_DB]
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            raise e

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")

    @classmethod
    def get_db(cls):
        return cls.db 