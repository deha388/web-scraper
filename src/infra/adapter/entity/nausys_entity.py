from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel


class PriceInfo(BaseModel):
    discounted_price: str
    original_price: str
    discount_percentage: Optional[str] = None


class BookingDetail(BaseModel):
    yacht_name: str
    status: str
    location: str
    prices: PriceInfo


class BookingPeriod(BaseModel):
    period_from: datetime
    period_to: datetime
    details: List[BookingDetail]


class DailyBookingData(BaseModel):
    competitor: str
    yacht_id: str
    last_update_date: datetime
    booking_periods: List[BookingPeriod]