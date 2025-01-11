from fastapi import APIRouter, Depends
from api.dto.bot_dto import BotStartRequest, BotStatusResponse
from api.controllers.mmk_controller import MMKController
from core.auth.jwt_handler import get_current_user

router = APIRouter()

@router.post("/start", response_model=BotStatusResponse)
async def start_bot(
    request: BotStartRequest,
    current_user = Depends(get_current_user)
):
    return await MMKController.start_bot(request) 