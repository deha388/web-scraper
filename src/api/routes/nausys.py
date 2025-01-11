from fastapi import APIRouter, Depends
from api.dto.bot_dto import BotStartRequest, BotStatusResponse
from api.controllers.nausys_controller import NausysController
from core.auth.jwt_handler import get_current_user

router = APIRouter()

@router.post("/start", response_model=BotStatusResponse)
async def start_bot(
    request: BotStartRequest,
    current_user = Depends(get_current_user)
):
    return await NausysController.start_bot(request) 