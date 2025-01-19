from fastapi import APIRouter, Depends
from src.api.dto.auth_dto import LoginRequest, LoginResponse
from src.api.controllers.auth_controller import AuthController

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    return await AuthController.login(request)
