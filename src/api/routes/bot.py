from fastapi import APIRouter, Depends, Request
from src.api.controllers.bot_controller import BotController
from src.api.dto.bot_dto import BotStatusResponse, BotType
from src.core.auth.jwt_handler import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_bot_controller(request: Request) -> BotController:

    return request.app.state.bot_controller


@router.post("/bot/start", response_model=BotStatusResponse)
async def start_bot(
        platform: BotType,
        current_user: str = Depends(get_current_user),
        bot_controller: BotController = Depends(get_bot_controller)
):
    return await bot_controller.start_bot(platform)


@router.post("/bot/stop", response_model=BotStatusResponse)
async def stop_nausys_bot(
        platform: BotType,
        current_user: str = Depends(get_current_user),
        bot_controller: BotController = Depends(get_bot_controller)
):
    return await bot_controller.stop_bot(platform)


@router.get("/bot/status", response_model=BotStatusResponse)
async def get_nausys_status(
        platform: BotType,
        current_user: str = Depends(get_current_user),
        bot_controller: BotController = Depends(get_bot_controller)
):
    return await bot_controller.get_bot_status(platform)
