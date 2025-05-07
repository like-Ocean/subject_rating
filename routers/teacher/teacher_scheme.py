from typing import Optional

from pydantic import BaseModel, Field


class CreateTeacherModel(BaseModel):
    first_name: str = Field(..., min_length=1)
    surname: str = Field(..., min_length=1)
    patronymic: Optional[str] = Field(None)


class UpdateTeacherModel(BaseModel):
    id: str = Field(..., description="teacher_id")
    first_name: str = Field(..., min_length=1)
    surname: str = Field(..., min_length=1)
    patronymic: Optional[str] = Field(None)


class DeleteTeacherModel(BaseModel):
    id: str = Field(..., description="teacher_id")


class AppointTeacherDisciplines(BaseModel):
    id: str = Field(..., description="teacher_id")
    discipline_ids: list[str] = Field(..., description="discipline_ids")


class RemoveTeacherDiscipline(BaseModel):
    id: str = Field(..., description="teacher_id")
    discipline_id: str = Field(...)
