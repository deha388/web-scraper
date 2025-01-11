from pydantic import BaseModel
from typing import List
from datetime import datetime

class BotStartRequest(BaseModel):
    platform: str
    competitor_ids: List[str]
    boat_ids: List[str]
    start_date: datetime
    end_date: datetime

class BotStatusResponse(BaseModel):
    platform: str
    status: str
    last_run: datetime
    next_run: datetime 