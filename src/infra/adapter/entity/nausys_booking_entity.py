from datetime import datetime
from typing import Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field, ConfigDict, GetJsonSchemaHandler, GetCoreSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {"type": "string"}

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.str_schema()
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

class NausysBookingEntity(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "yacht_id": "34432275",
                "period_from": "2025-04-12T00:00:00",
                "period_to": "2025-04-19T00:00:00",
                "price": 2500.00,
                "currency": "EUR",
                "status": "available",
                "raw_data": {}
            }
        }
    )

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    yacht_id: str
    period_from: datetime
    period_to: datetime
    price: float
    currency: str
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Dict[str, Any] 