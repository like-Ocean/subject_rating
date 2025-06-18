from typing import Optional
from pydantic import BaseModel, UUID4, Field
from .AdminResponse import ModuleBaseResponse
from routers.discipline.discipline_scheme import DisciplineFormat


class DisciplineResponse(BaseModel):
    id: UUID4 = Field(
        ...,
        description="ID дисциплины",
        example="c56a4180-65aa-42ec-a945-5fd21dec0538"
    )
    name: str = Field(
        ...,
        description="Название дисциплины",
        example="Теория вероятностей"
    )
    format: DisciplineFormat = Field(
        ...,
        description="Формат дисциплины",
        example=DisciplineFormat.traditional
    )
    description: Optional[str] = Field(
        None,
        description="Описание дисциплины",
        example="Курс по базовым понятиям теории вероятностей"
    )
    modeus_link: Optional[str] = Field(
        None,
        description="Ссылка на Modeus",
        example="https://modeus.example.com/discipline/123"
    )
    presentation_link: Optional[str] = Field(
        None,
        description="Ссылка на презентацию",
        example="https://slides.example.com/discipline/123"
    )
    module: ModuleBaseResponse = Field(
        ...,
        description="Данные модуля, к которому относится дисциплина"
    )
    avg_rating: float = Field(
        ...,
        description="Средний рейтинг по отзывам",
        example=4.2
    )
    review_count: int = Field(
        ...,
        description="Количество опубликованных отзывов",
        example=17
    )
    favorites_count: int = Field(
        ...,
        description="Сколько раз добавляли в избранное",
        example=5
    )
    is_favorite: bool = Field(
        False,
        description="Пользователь добавил в избранное?",
        example=True
    )
