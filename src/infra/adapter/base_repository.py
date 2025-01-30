from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Any, Dict, List


class BaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def create_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        result = await self._db[collection_name].insert_one(document)
        return str(result.inserted_id)

    async def create_many(self, collection_name: str, documents: List[Dict[str, Any]]):
        result = await self._db[collection_name].insert_many(documents)
        return [str(inserted_id) for inserted_id in result.inserted_ids]

    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        doc = await self._db[collection_name].find_one(query)
        print(doc)
        return doc

    async def find_many(self, collection_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        cursor = self._db[collection_name].find(query)
        results = []
        async for document in cursor:
            results.append(document)
        return results

    async def update_one(self, collection_name: str, query: Dict[str, Any], update_data: Dict[str, Any]):
        result = await self._db[collection_name].update_one(query, update_data)
        return result.modified_count

    async def delete_one(self, collection_name: str, query: Dict[str, Any]):
        result = await self._db[collection_name].delete_one(query)
        return result.deleted_count
