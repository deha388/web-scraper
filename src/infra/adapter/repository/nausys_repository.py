from datetime import datetime
from typing import List, Optional
from src.infra.adapter.entity.nausys_entity import NausysCompanyData
from src.infra.adapter.interface.repository_interface import RepositoryInterface
from src.infra.config.database import config
from src.infra.config.settings import MONGO_DB
import logging

logger = logging.getLogger(__name__)

class NausysRepository(RepositoryInterface[NausysCompanyData]):
    def __init__(self):
        self.session = config.db_session
        self.db = self.session[MONGO_DB]

    def get_collection_name(self, company_id: str) -> str:
        """Generate collection name based on company and date"""
        current_date = datetime.utcnow().strftime("%Y%m%d")
        return f"nausys_{company_id}_{current_date}"

    async def save(self, data: NausysCompanyData) -> bool:
        """Save company data to its specific collection"""
        try:
            collection_name = self.get_collection_name(data.company_id)
            collection = self.db[collection_name]
            
            # Convert to dict and save
            await collection.insert_one(data.model_dump())
            logger.info(f"Saved data for company {data.company_name} to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving company data: {str(e)}")
            return False

    async def get_latest(self, identifier: str) -> Optional[NausysCompanyData]:
        """Get latest data for a specific company"""
        try:
            collection_name = self.get_collection_name(identifier)
            collection = self.db[collection_name]
            
            # Get the most recent record
            data = await collection.find_one(
                sort=[("created_at", -1)]
            )
            
            if data:
                return NausysCompanyData(**data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting company data: {str(e)}")
            return None

    async def get_by_date(self, identifier: str, date: datetime) -> Optional[NausysCompanyData]:
        """Get company data for a specific date"""
        try:
            collection_name = f"nausys_{identifier}_{date.strftime('%Y%m%d')}"
            collection = self.db[collection_name]
            
            data = await collection.find_one(
                sort=[("created_at", -1)]
            )
            
            if data:
                return NausysCompanyData(**data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting company data by date: {str(e)}")
            return None

    async def get_all_latest(self) -> List[NausysCompanyData]:
        """Get latest data for all companies"""
        try:
            # Get all collections that start with 'nausys_'
            collections = await self.db.list_collection_names(
                filter={"name": {"$regex": "^nausys_"}}
            )
            
            results = []
            for collection_name in collections:
                if collection_name.startswith("nausys_"):
                    collection = self.db[collection_name]
                    data = await collection.find_one(
                        sort=[("created_at", -1)]
                    )
                    if data:
                        results.append(NausysCompanyData(**data))
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting all companies data: {str(e)}")
            return [] 