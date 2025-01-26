from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infra.adapter.base_repository import BaseRepository


class CompetitorRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.collection_name = "competitor"

    async def upsert_competitor_info(
        self,
        competitor_name: str,
        yacht_ids: Dict[str, str],
        search_text: str,
        click_text: str
    ):
        existing_doc = await self.find_one(self.collection_name, {"competitor_name": competitor_name})
        if existing_doc:
            update_data = {
                "$set": {
                    "yacht_ids": yacht_ids,
                    "search_text": search_text,
                    "click_text": click_text
                }
            }
            await self.update_one(self.collection_name, {"competitor_name": competitor_name}, update_data)
        else:
            doc = {
                "competitor_name": competitor_name,
                "yacht_ids": yacht_ids,
                "search_text": search_text,
                "click_text": click_text
            }
            await self.create_one(self.collection_name, doc)

    async def get_competitor_doc(self, competitor_name: str) -> Dict[str, Any]:
        return await self.find_one(self.collection_name, {"competitor_name": competitor_name})

    async def get_all_competitors_and_yacht_ids(self) -> Dict[str, List[str]]:
        docs = await self.find_many(self.collection_name, {})
        result = {}
        for doc in docs:
            cname = doc["competitor_name"]
            yids = doc.get("yacht_ids", [])
            result[cname] = yids
        return result
