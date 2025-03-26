from datetime import datetime, date
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infra.adapter.base_repository import BaseRepository


class BookingDataRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: None = "booking_data"):
        super().__init__(db)
        self.collection_name = collection_name

    async def save_daily_booking_data(
            self,
            competitor: str,
            booking_docs: List[Dict[str, Any]]
    ):
        docs_to_insert = []
        for doc in booking_docs:
            doc["competitor"] = competitor
            doc["last_update_date"] = datetime.now()

            docs_to_insert.append(doc)

        if docs_to_insert:
            await self._db[self.collection_name].insert_many(docs_to_insert)

    async def get_daily_booking_data(
            self,
            competitor: str,
            yacht_id: str,
            query_date: date
    ) -> Dict[str, Any]:

        filter_ = {
            "competitor": competitor,
            "yacht_id": yacht_id,
            "last_update_date": datetime(query_date.year, query_date.month, query_date.day, 0, 0, 0)
        }
        doc = await self.find_one(self.collection_name, filter_)
        return doc

    async def get_booking_data_in_date_range(
            self,
            competitor: str,
            yacht_id: str,
            start_date: date,
            end_date: date
    ) -> List[Dict[str, Any]]:

        filter_ = {
            "competitor": competitor,
            "yacht_id": yacht_id,
            "last_update_date": {
                "$gte": datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0),
                "$lte": datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            }
        }
        docs = await self.find_many(self.collection_name, filter_)
        return docs

    async def find_booking_doc(
            self,
            competitor: str,
            yacht_id: str
    ) -> Optional[Dict[str, Any]]:

        query = {
            "competitor": competitor,
            "yacht_id": yacht_id
        }

        doc = await self._db[self.collection_name].find_one(
            filter=query,
            sort=[("last_update_date", -1)]
        )

        return doc
