from typing import List, Dict, Optional
from datetime import datetime
from infra.mongodb.collections.prices import Price
from infra.mongodb.connection import MongoDB

class PriceRepository:
    collection_name = "prices"

    @classmethod
    async def save_weekly_prices(cls, prices: List[Price]):
        collection = MongoDB.get_db()[cls.collection_name]
        price_data = [price.dict() for price in prices]
        await collection.insert_many(price_data)

    @classmethod
    async def get_prices_by_date_range(
        cls, 
        platform: str,
        start_date: datetime, 
        end_date: datetime, 
        competitor_id: Optional[str] = None,
        boat_id: Optional[str] = None
    ) -> List[Price]:
        collection = MongoDB.get_db()[cls.collection_name]
        
        query = {
            "platform": platform,
            "week_start": {"$gte": start_date},
            "week_end": {"$lte": end_date}
        }
        
        if competitor_id:
            query["competitor_id"] = competitor_id
        if boat_id:
            query["boat_id"] = boat_id

        cursor = collection.find(query).sort("week_start", -1)
        return [Price(**doc) for doc in await cursor.to_list(length=None)] 