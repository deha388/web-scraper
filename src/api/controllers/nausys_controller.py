from .base_bot_controller import BaseBotController
from fastapi import HTTPException
from datetime import datetime, timedelta
from core.bot.nausys import NausysTracker
from api.dto.bot_dto import BotStartRequest, BotStatusResponse

class NausysController(BaseBotController):
    @classmethod
    async def start_bot(cls, request: BotStartRequest) -> BotStatusResponse:
        try:
            if super().start_bot("nausys"):
                return BotStatusResponse(
                    platform="nausys",
                    status="running",
                    last_run=datetime.utcnow(),
                    next_run=datetime.utcnow() + timedelta(minutes=1)
                )
            return BotStatusResponse(
                platform="nausys",
                status="already_running",
                last_run=cls.get_status("nausys").get('last_run'),
                next_run=datetime.utcnow() + timedelta(minutes=1)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @classmethod
    async def stop_bot(cls) -> BotStatusResponse:
        if super().stop_bot("nausys"):
            return BotStatusResponse(
                platform="nausys",
                status="stopped",
                last_run=cls.get_status("nausys").get('last_run'),
                next_run=None
            )
        raise HTTPException(status_code=404, detail="Bot not found") 