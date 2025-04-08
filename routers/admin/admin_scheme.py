from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class AddAdminModel(BaseModel):
    target_user_id: str = Field(...)


class RemoveAdminModel(BaseModel):
    target_user_id: str = Field(...)


class AddModuleModel(BaseModel):
    name: str = Field(...)


class DeleteModuleModel(BaseModel):
    module_id: str = Field(...)


class UpdateModuleModel(BaseModel):
    module_id: str = Field(...)
    new_name: str = Field(...)


class CreateTeacherModel(BaseModel):
    first_name: str = Field(..., min_length=1)
    surname: str = Field(..., min_length=1)
    patronymic: Optional[str] = Field(None)


class UpdateTeacherModel(BaseModel):
    teacher_id: str = Field(...)
    first_name: str = Field(..., min_length=1)
    surname: str = Field(..., min_length=1)
    patronymic: Optional[str] = Field(None)


class DeleteTeacherModel(BaseModel):
    teacher_id: str = Field(...)


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
    name: str = Field(..., min_length=1)
    format: DisciplineFormat = Field(...)
    description: Optional[str] = Field(None)
    modeus_link: Optional[str] = Field(None)
    presentation_link: Optional[str] = Field(None)
    module_id: str = Field(...)


class DeleteDisciplineModel(BaseModel):
    discipline_id: str = Field(...)


class AppointTeacherDiscipline(BaseModel):
    teacher_id: str = Field(...)
    discipline_id: str = Field(...)
