from typing import Optional
from datetime import datetime
from infra.mongodb.collections.users import User
from infra.mongodb.connection import MongoDB

class UserRepository:
    collection_name = "users"

    @classmethod
    async def create_user(cls, user: User) -> str:
        collection = MongoDB.get_db()[cls.collection_name]
        result = await collection.insert_one(user.dict())
        return str(result.inserted_id)

    @classmethod
    async def get_user_by_email(cls, email: str) -> Optional[User]:
        collection = MongoDB.get_db()[cls.collection_name]
        user_data = await collection.find_one({"email": email})
        return User(**user_data) if user_data else None

    @classmethod
    async def update_last_login(cls, email: str):
        collection = MongoDB.get_db()[cls.collection_name]
        await collection.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.utcnow()}}
        ) 