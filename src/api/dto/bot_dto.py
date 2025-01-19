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


class BotIntervalRequest(BaseModel):
    interval_minutes: Optional[int] = 60  # Default to run every hour


class BotStatusResponse(BaseModel):
    bot_type: BotType
    status: BotStatus
    message: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
