from typing import Optional

from pydantic import BaseModel, Field


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


class AppointTeacherDisciplines(BaseModel):
    teacher_id: str = Field(...)
    discipline_ids: list[str] = Field(...)


class RemoveTeacherDiscipline(BaseModel):
    teacher_id: str = Field(...)
    discipline_id: str = Field(...)
