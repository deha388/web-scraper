# src/infra/adapter/booking_data_repository.py

from datetime import datetime, date
from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infra.adapter.base_repository import BaseRepository


class BookingDataRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.collection_name = "booking_data"  # Tek koleksiyon adı

    from datetime import datetime, date, time

    ...

    async def save_daily_booking_data(
            self,
            competitor: str,
            booking_docs: List[Dict[str, Any]]
    ):
        for doc in booking_docs:
            doc["competitor"] = competitor

            # last_update_date 'date' ise:
            if isinstance(doc.get("last_update_date"), date):
                # date -> datetime (saat, dakika = 0)
                d = doc["last_update_date"]
                doc["last_update_date"] = datetime(d.year, d.month, d.day, 0, 0, 0)
            elif isinstance(doc.get("last_update_date"), str):
                # Örneğin "2025-01-29" gibi bir string ise datetime'a parse edebiliriz
                d = date.fromisoformat(doc["last_update_date"])  # date objesi
                doc["last_update_date"] = datetime(d.year, d.month, d.day, 0, 0, 0)
            else:
                # Eğer hiç yoksa bugünün datetime'ı
                doc["last_update_date"] = datetime.now()

            filter_ = {
                "competitor": doc["competitor"],
                "yacht_id": doc["yacht_id"],
                # Artık 'last_update_date' bir datetime.datetime
                "last_update_date": doc["last_update_date"]
            }

            update_ = {
                "$set": {
                    "booking_periods": doc["booking_periods"]
                }
            }

            await self._db[self.collection_name].update_one(filter_, update_, upsert=True)

    async def get_daily_booking_data(
            self,
            competitor: str,
            yacht_id: str,
            query_date: date
    ) -> Dict[str, Any]:
        filter_ = {
            "competitor": competitor,
            "yacht_id": yacht_id,
            "last_update_date": query_date
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
                "$gte": start_date,
                "$lte": end_date
            }
        }
        docs = await self.find_many(self.collection_name, filter_)
        return docs
