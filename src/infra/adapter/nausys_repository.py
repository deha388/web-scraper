import datetime
from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infra.adapter.base_repository import BaseRepository


class NausysRepository(BaseRepository):

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)

    async def save_booking_data(
            self,
            competitor_name: str,
            booking_data: List[Dict[str, Any]]
    ):
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        collection_name = f"nausys_{competitor_name}_{today_str}"
        if booking_data:
            inserted_ids = await self.create_many(collection_name, booking_data)
            return inserted_ids
        return None
