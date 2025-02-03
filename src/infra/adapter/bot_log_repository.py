from src.infra.adapter.base_repository import BaseRepository
from motor.motor_asyncio import AsyncIOMotorDatabase


class BotLogRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.collection_name = "bot_log"
