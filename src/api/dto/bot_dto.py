from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class BotStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class BotType(str, Enum):
    NAUSYS = "nausys"
    MMK = "mmk"


class BotStatusResponse(BaseModel):
    bot_type: BotType
    status: BotStatus
    message: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    bot_last_started: Optional[datetime] = None


class BotDailyStatusResponse(BaseModel):
    bot_id: int
    status: str
    last_update_date: Optional[datetime] = None
    timestamp: Optional[datetime] = None
