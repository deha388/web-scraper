# src/api/routes/nausys_bot.py

from fastapi import APIRouter, Depends, Request
from src.api.controllers.bot_controller import BotController
from src.api.dto.bot_dto import BotIntervalRequest, BotStatusResponse, BotType
from src.core.auth.jwt_handler import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_bot_controller(request: Request) -> BotController:
    # app.state.bot_controller gibi tek bir instance
    return request.app.state.bot_controller


@router.post("/start", response_model=BotStatusResponse)
async def start_nausys_bot(
    request: BotIntervalRequest = BotIntervalRequest(),
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """
    Nausys botu başlat: eksik data varsa hemen doldur, sonrasında her gece 00:00 çalışsın.
    """
    return await bot_controller.start_bot(BotType.NAUSYS, request.interval_minutes)


@router.post("/stop", response_model=BotStatusResponse)
async def stop_nausys_bot(
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Nausys botu durdur."""
    return await bot_controller.stop_bot(BotType.NAUSYS)


@router.get("/status", response_model=BotStatusResponse)
async def get_nausys_status(
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Nausys botunun o anki durumunu döndür."""
    return await bot_controller.get_bot_status(BotType.NAUSYS)
