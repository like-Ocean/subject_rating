from pydantic import BaseModel, UUID4, Field
from datetime import datetime


class ModuleBaseResponse(BaseModel):
    id: UUID4 = Field(
        ...,
        description="Module ID",
        example="f47ac10b-58cc-4372-a567-0e02b2c3d479"
    )
    name: str = Field(
        ...,
        description="Название модуля",
        example="Математика"
    )


class ModuleResponse(ModuleBaseResponse):
    created_at: datetime = Field(
        ...,
        description="Дата и время создания модуля",
        example="2025-04-28T14:22:33.123Z"
    )
