from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DisciplineFormat(str, Enum):
    online = "онлайн"
    traditional = "традиционный"
    mixed = "смешанный"


class CreateDisciplineModel(BaseModel):
    name: str = Field(..., min_length=1)
    format: DisciplineFormat = Field(...)
    description: Optional[str] = Field(None)
    modeus_link: Optional[str] = Field(None)
    presentation_link: Optional[str] = Field(None)
    module_id: str = Field(...)


class UpdateDisciplineModel(BaseModel):
    discipline_id: str = Field(...)
    name: Optional[str] = None
    format_value: Optional[DisciplineFormat] = Field(None)
    module_id: Optional[str] = Field(None)
    description: Optional[str] = None
    modeus_link: Optional[str] = None
    presentation_link: Optional[str] = None


class DeleteDisciplineModel(BaseModel):
    discipline_id: str = Field(...)
