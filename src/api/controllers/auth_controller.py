from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
from core.auth.jwt_handler import create_access_token
from core.auth.password_handler import verify_password
from infra.repositories.user_repository import UserRepository
from api.dto.auth_dto import LoginRequest, LoginResponse

class AuthController:
    @staticmethod
    async def login(request: LoginRequest) -> LoginResponse:
        user = await UserRepository.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        await UserRepository.update_last_login(request.email)
        
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(hours=24)
        )
        
        return LoginResponse(access_token=access_token) 