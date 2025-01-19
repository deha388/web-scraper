from pydantic import BaseModel
from typing import Optional, List


class PriceInfo(BaseModel):
    discounted_price: str
    original_price: str
    discount_percentage: Optional[str]


class BookingDetail(BaseModel):
    yacht_name: str
    status: str
    location: str
    prices: PriceInfo


class BookingPeriod(BaseModel):
    period_from: str
    period_to: str
    details: List[BookingDetail]


class CompanyResult(BaseModel):
    yacht_id: str
    booking_periods: List[BookingPeriod]
