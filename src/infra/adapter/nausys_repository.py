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

    async def upsert_competitor_yacht_ids(
        self,
        competitor_name: str,
        yacht_ids: List[str]
    ):
        """
        competitor adlı koleksiyonda, competitor_name alanı eşleşen bir doküman varsa
        -> 'yacht_ids' alanını tamamen yeni listeyle günceller (replace).
        Yoksa -> yeni bir doküman oluşturur.

        Örnek doküman (competitor koleksiyonunda):
         {
           "competitor_name": "rudder",
           "yacht_ids": ["yat_id_1", "yat_id_2", ...]
         }
        """
        collection_name = "competitor"  # Sabit isim
        # Önce var mı diye kontrol
        existing_doc = await self.find_one(collection_name, {"competitor_name": competitor_name})
        if existing_doc:
            # Güncelle
            await self.update_one(
                collection_name,
                {"competitor_name": competitor_name},
                {"$set": {"yacht_ids": yacht_ids}}
            )
        else:
            # Insert
            doc = {
                "competitor_name": competitor_name,
                "yacht_ids": yacht_ids
            }
            await self.create_one(collection_name, doc)

    async def get_competitor_yacht_ids(self, competitor_name: str) -> List[str]:
        """
        Tek bir rakibin (competitor_name) kayıtlı olan yat ID’lerini getirir.
        Eşleşen doküman yoksa boş liste döndürür.
        """
        collection_name = "competitor"
        doc = await self.find_one(collection_name, {"competitor_name": competitor_name})
        if doc:
            # 'yacht_ids' alanı yoksa default []
            return doc.get("yacht_ids", [])
        return []

    async def get_all_competitors(self) -> List[Dict[str, Any]]:
        """
        competitor koleksiyonundaki tüm dokümanları döndürür.
        Örnek dönüş:
         [
           {
             "competitor_name": "rudder",
             "yacht_ids": ["yat_id_1", "yat_id_2"]
           },
           {
             "competitor_name": "some_other",
             "yacht_ids": ["yat_id_10"]
           }
         ]
        """
        collection_name = "competitor"
        docs = await self.find_many(collection_name, {})
        return docs

    async def get_all_competitors_and_yacht_ids(self) -> Dict[str, List[str]]:
        """
        Tüm rakipleri ve onların yat id listelerini
        {'rudder': ['yat_id_1','yat_id_2'], 'some_other': [...]} formatında döndürür.
        """
        collection_name = "competitor"
        docs = await self.find_many(collection_name, {})
        result = {}
        for doc in docs:
            cname = doc["competitor_name"]
            yids = doc.get("yacht_ids", [])
            result[cname] = yids
        return result
