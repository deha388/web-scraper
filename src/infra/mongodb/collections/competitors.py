from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class Competitor(BaseModel):
    name: str
    platform: str  # 'nausys' veya 'mmk'
    platform_id: str
    boats: List[str]  # takip edilen teknelerin ID'leri
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_updated: datetime = datetime.utcnow() 