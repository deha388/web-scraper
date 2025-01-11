from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class Price(BaseModel):
    platform: str  # 'nausys' veya 'mmk'
    competitor_id: str
    boat_id: str
    week_start: datetime
    week_end: datetime
    price: float
    our_price: float
    price_diff: float
    status: str  # 'high', 'normal', 'low'
    created_at: datetime = datetime.utcnow() 