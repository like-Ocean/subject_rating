from typing import List
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from .AdminResponse import ModuleBaseResponse


class TeacherDisciplineResponse(BaseModel):
    id: UUID4 = Field(..., example="c56a4180-65aa-42ec-a945-5fd21dec0538")
    name: str = Field(..., example="Теория вероятностей")
    module: ModuleBaseResponse


class TeacherResponse(BaseModel):
    id: UUID4 = Field(..., example="a3d7b9d0-4b5a-4c3d-8e2a-0f0b8d5c5e5a")
    first_name: str = Field(..., example="Иван")
    surname: str = Field(..., example="Иванов")
    patronymic: Optional[str] = Field(None, example="Петрович")
    disciplines: List[TeacherDisciplineResponse] = Field(...)
