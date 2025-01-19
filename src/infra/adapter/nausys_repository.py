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

    async def get_booking_data(
            self,
            competitor_name: str,
            query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        collection_name = f"nausys_{competitor_name}_{today_str}"
        booking_data = await self.find_many(collection_name, query)
        return booking_data

    async def save_yacht_ids(self, competitor_name: str, yacht_ids: List[str]):

        if not yacht_ids:
            return None

        collection_name = "nausys_firm_yachts"
        docs_to_insert = []
        now_utc = datetime.datetime.utcnow()

        for yid in yacht_ids:
            doc = {
                "competitor_name": competitor_name,
                "yacht_id": yid,
                "inserted_at": now_utc
            }
            docs_to_insert.append(doc)

        inserted_ids = await self.create_many(collection_name, docs_to_insert)
        return inserted_ids

    async def get_yacht_ids_for_competitor(self, competitor_name: str) -> List[str]:
        collection_name = "nausys_firm_yachts"
        query = {"competitor_name": competitor_name}

        documents = await self.find_many(collection_name, query)
        yacht_id_set = set()
        for doc in documents:
            yacht_id_set.add(doc["yacht_id"])

        return list(yacht_id_set)

    async def get_all_companies_and_yacht_ids(self) -> Dict[str, List[str]]:

        collection_name = "nausys_firm_yachts"
        all_docs = await self.find_many(collection_name, {})

        results = {}
        for doc in all_docs:
            competitor = doc["competitor_name"]
            yid = doc["yacht_id"]
            if competitor not in results:
                results[competitor] = []

            if yid not in results[competitor]:
                results[competitor].append(yid)

        return results
