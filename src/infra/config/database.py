from motor.motor_asyncio import AsyncIOMotorClient
from typing import List


class DatabaseConfig:
    def __init__(self):
        self._database_url = None
        self._db_client = None

    @property
    def database_url(self) -> str:
        return self._database_url

    @database_url.setter
    def database_url(self, value: str):
        self._database_url = value

    @property
    def db_session(self):
        if not self._db_client:
            self._db_client = AsyncIOMotorClient(self._database_url)

        return self._db_client

    def check(self) -> List[str]:
        errors = []
        if not self._database_url:
            errors.append("FATAL: DATABASE CONFIG -> DATABASE URL not set")

        return errors


config = DatabaseConfig()
