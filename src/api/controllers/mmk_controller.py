from fastapi import HTTPException
from datetime import datetime, timedelta
from core.bot.mmk import MMKTracker
from infra.repositories.price_repository import PriceRepository
from api.dto.bot_dto import BotStartRequest, BotStatusResponse

class MMKController:
    @staticmethod
    async def start_bot(request: BotStartRequest) -> BotStatusResponse:
        try:
            bot = MMKTracker()
            bot.setup_driver()
            if not bot.login():
                raise HTTPException(status_code=500, detail="MMK login failed")
            
            # Bot işlemleri...
            
            return BotStatusResponse(
                platform="mmk",
                status="running",
                last_run=datetime.utcnow(),
                next_run=datetime.utcnow() + timedelta(hours=1)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 