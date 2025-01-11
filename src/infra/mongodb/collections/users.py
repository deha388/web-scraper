from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class User(BaseModel):
    email: EmailStr
    password_hash: str
    full_name: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None 