from fastapi import APIRouter, Depends, Request
from src.core.bot_controller import BotController
from src.api.dto.bot_dto import BotIntervalRequest, BotStatusResponse, BotType
from src.core.auth.jwt_handler import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_bot_controller(request: Request) -> BotController:
    return BotController(request.app.state.db)


# Nausys Bot Endpoints
@router.post("/nausys/start", response_model=BotStatusResponse)
async def start_nausys_bot(
    request: BotIntervalRequest = BotIntervalRequest(),
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """
    Start the Nausys bot with optional interval settings
    - interval_minutes: How often the bot should run (default: 60 minutes)
    """
    return await bot_controller.start_bot(BotType.NAUSYS, request.interval_minutes)


@router.post("/nausys/stop", response_model=BotStatusResponse)
async def stop_nausys_bot(
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Stop the Nausys bot"""
    return await bot_controller.stop_bot(BotType.NAUSYS)


@router.get("/nausys/status", response_model=BotStatusResponse)
async def get_nausys_status(
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Get the current status of Nausys bot"""
    return await bot_controller.get_bot_status(BotType.NAUSYS)


# MMK Bot Endpoints
@router.post("/mmk/start", response_model=BotStatusResponse)
async def start_mmk_bot(
    request: BotIntervalRequest = BotIntervalRequest(),
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """
    Start the MMK bot with optional interval settings
    - interval_minutes: How often the bot should run (default: 60 minutes)
    """
    return await bot_controller.start_bot(BotType.MMK, request.interval_minutes)


@router.post("/mmk/stop", response_model=BotStatusResponse)
async def stop_mmk_bot(
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Stop the MMK bot"""
    return await bot_controller.stop_bot(BotType.MMK)


@router.get("/mmk/status", response_model=BotStatusResponse)
async def get_mmk_status(
    current_user: str = Depends(get_current_user),
    bot_controller: BotController = Depends(get_bot_controller)
):
    """Get the current status of MMK bot"""
    return await bot_controller.get_bot_status(BotType.MMK)
