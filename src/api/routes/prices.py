from fastapi import APIRouter, Depends
from src.infra.config.settings import MONGO_DB
from src.infra.config.database import config
from datetime import datetime, timedelta
from src.core.auth.jwt_handler import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/latest")
async def get_latest_prices(current_user: str = Depends(get_current_user)):
    """Get the latest prices for all boats"""
    try:
        session = config.db_session
        db = session[MONGO_DB]
        # Get prices from last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        cursor = db.prices.find(
            {"created_at": {"$gte": cutoff_time}},
            sort=[("created_at", -1)]
        )

        prices = await cursor.to_list(length=100)
        return {"status": "success", "data": prices}

    except Exception as e:
        logger.error(f"Error fetching latest prices: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/competitor/{competitor_id}")
async def get_competitor_prices(competitor_id: str, current_user: str = Depends(get_current_user)):
    """Get prices for a specific competitor"""
    try:
        session = config.db_session
        db = session[MONGO_DB]
        cursor = db.prices.find(
            {"competitor_id": competitor_id},
            sort=[("created_at", -1)],
            limit=100
        )

        prices = await cursor.to_list(length=100)
        return {"status": "success", "data": prices}

    except Exception as e:
        logger.error(f"Error fetching competitor prices: {str(e)}")
        return {"status": "error", "message": str(e)}
