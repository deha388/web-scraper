# src/infra/adapter/nausys_repository.py

import datetime
from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infra.adapter.base_repository import BaseRepository


class NausysRepository(BaseRepository):
    """
    competitor koleksiyonunda:
      {
        "competitor_name": str,
        "yacht_ids": list[str],
        "search_text": str,
        "click_text": str
      }

    Rezervasyon verileri:
      nausys_{competitor_name}_{YYYYMMDD}
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)

    # -------------------------------
    # 1) Booking Data Kaydetme
    # -------------------------------
    async def save_booking_data(
            self,
            competitor_name: str,
            booking_data: List[Dict[str, Any]]
    ):
        """
        Bugünün tarihine göre (YYYYMMDD) nausys_{competitor_name}_{yyyyMMdd} koleksiyonuna ekler.
        """
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
        """
        Bugünün tarihli koleksiyon içinde sorgu.
        """
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        collection_name = f"nausys_{competitor_name}_{today_str}"
        booking_data = await self.find_many(collection_name, query)
        return booking_data

    # -------------------------------
    # 2) Competitor Koleksiyonu
    # -------------------------------
    async def upsert_competitor_info(
        self,
        competitor_name: str,
        yacht_ids: List[str],
        search_text: str,
        click_text: str
    ):
        """
        competitor koleksiyonunda, competitor_name alanını bulur.
         -> yoksa insert, varsa update.
        """
        collection_name = "competitor"
        existing_doc = await self.find_one(collection_name, {"competitor_name": competitor_name})
        if existing_doc:
            await self.update_one(
                collection_name,
                {"competitor_name": competitor_name},
                {
                    "$set": {
                        "yacht_ids": yacht_ids,
                        "search_text": search_text,
                        "click_text": click_text
                    }
                }
            )
        else:
            doc = {
                "competitor_name": competitor_name,
                "yacht_ids": yacht_ids,
                "search_text": search_text,
                "click_text": click_text
            }
            await self.create_one(collection_name, doc)

    async def get_competitor_doc(self, competitor_name: str) -> Dict[str, Any]:
        """
        Tek bir rakip dokümanını döndürür.
        {
          "competitor_name": ...,
          "yacht_ids": [...],
          "search_text": "...",
          "click_text": "..."
        }
        """
        return await self.find_one("competitor", {"competitor_name": competitor_name})

    async def get_all_competitors_and_yacht_ids(self) -> Dict[str, List[str]]:
        """
        Tüm rakiplerin {'name': [...yid...], ...} formatında dön.
        """
        docs = await self.find_many("competitor", {})
        result = {}
        for doc in docs:
            cname = doc["competitor_name"]
            yids = doc.get("yacht_ids", [])
            result[cname] = yids
        return result

    async def get_competitors_missing_data_for_today(self) -> Dict[str, List[str]]:
        """
        Bugün (YYYYMMDD) verisi olmayan rakipleri bul. (Herhangi bir kayıt yoksa missing sayar.)
        """
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        all_competitors = await self.get_all_competitors_and_yacht_ids()
        missing_dict = {}

        for competitor_name, yacht_ids in all_competitors.items():
            if not yacht_ids:
                continue
            coll_name = f"nausys_{competitor_name}_{today_str}"
            doc = await self.find_one(coll_name, {})
            if not doc:
                missing_dict[competitor_name] = yacht_ids

        return missing_dict
