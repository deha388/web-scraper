from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class RepositoryInterface(ABC, Generic[T]):
    """Generic repository interface for all data operations"""

    @abstractmethod
    async def save(self, data: T) -> bool:
        """Save data to repository"""
        pass

    @abstractmethod
    async def get_latest(self, identifier: str) -> Optional[T]:
        """Get latest data by identifier"""
        pass

    @abstractmethod
    async def get_by_date(self, identifier: str, date: datetime) -> Optional[T]:
        """Get data by identifier and date"""
        pass

    @abstractmethod
    async def get_all_latest(self) -> List[T]:
        """Get all latest data"""
        pass
