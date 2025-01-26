from fastapi import HTTPException
from src.api.dto.auth_dto import LoginRequest, LoginResponse
from src.core.auth.jwt_handler import create_access_token
from src.infra.config import settings


class AuthController:
    @staticmethod
    async def login(request: LoginRequest) -> LoginResponse:
        print(request.username)
        print(request.password)
        if request.username == settings.ADMIN_USERNAME and request.password == settings.ADMIN_PASSWORD:
            token = create_access_token({"sub": request.username})
            return LoginResponse(access_token=token)
        raise HTTPException(status_code=401, detail="Invalid credentials")
