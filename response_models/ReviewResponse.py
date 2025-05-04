from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime
from models.ReviewDiscipline import ReviewStatusEnum
from .AdminResponse import ModuleBaseResponse


class Author(BaseModel):
    id: UUID4 = Field(
        ...,
        description="Уникальный идентификатор автора",
        example="a3d7b9d0-4b5a-4c3d-8e2a-0f0b8d5c5e5a"
    )
    first_name: str = Field(
        ...,
        description="Имя автора",
        example="Иван"
    )
    surname: str = Field(
        ...,
        description="Фамилия автора",
        example="Иванов"
    )
    patronymic: Optional[str] = Field(
        None,
        description="Отчество автора (при наличии)",
        example="Иванович"
    )


class Lector(BaseModel):
    id: UUID4 = Field(
        ...,
        description="Уникальный идентификатор лектора",
        example="b4e6f8a2-1c4e-4d2a-9f3b-6a7c8d9e0f1b"
    )
    first_name: str = Field(
        ...,
        description="Имя лектора",
        example="Петр"
    )
    surname: str = Field(
        ...,
        description="Фамилия лектора",
        example="Петров"
    )
    patronymic: Optional[str] = Field(
        None,
        description="Отчество лектора (при наличии)",
        example="Сергеевич"
    )


class Practic(BaseModel):
    id: UUID4 = Field(
        ...,
        description="Уникальный идентификатор преподавателя практики",
        example="c5f7a9b3-2d5f-4e3a-8g4c-1b2c3d4e5f6g"
    )
    first_name: str = Field(
        ...,
        description="Имя преподавателя",
        example="Мария"
    )
    surname: str = Field(
        ...,
        description="Фамилия преподавателя",
        example="Сидорова"
    )
    patronymic: Optional[str] = Field(
        None,
        description="Отчество преподавателя (при наличии)",
        example="Алексеевна"
    )


class Discipline(BaseModel):
    id: UUID4 = Field(
        ...,
        description="Уникальный идентификатор дисциплины",
        example="e326f9b1-bf60-4a2b-9c7d-8e3f4a5b6c7d"
    )
    name: str = Field(
        ...,
        description="Название дисциплины",
        example="Дифференциальные уравнения"
    )
    module: ModuleBaseResponse = Field(
        ...,
        description="Модуль, к которому относится дисциплина"
    )


class ReviewResponse(BaseModel):
    id: UUID4 = Field(
        ...,
        description="Уникальный идентификатор отзыва",
        example="f437a8c2-d9e1-4b3f-8c5d-6a7b8c9d0e1f"
    )
    grade: int = Field(
        ...,
        description="Оценка (от 1 до 5)",
        example=5,
        ge=1,
        le=5
    )
    comment: Optional[str] = Field(
        None,
        description="Текст отзыва",
        example="Отличный курс с понятными объяснениями"
    )
    status: ReviewStatusEnum = Field(
        ...,
        description="Статус модерации отзыва"
    )
    author: Optional[Author] = Field(
        None,
        description="Автор отзыва (если не анонимный)"
    )
    discipline: Discipline = Field(
        ...,
        description="Дисциплина, к которой относится отзыв"
    )
    lector: Lector = Field(
        ...,
        description="Преподаватель-лектор"
    )
    practic: Practic = Field(
        ...,
        description="Преподаватель практики"
    )
    offensive_score: float = Field(
        ...,
        description="Уровень нарушения правил (0-1)",
        example=0.12
    )
    is_anonymous: bool = Field(
        default=False,
        description="Анонимный ли отзыв",
        example=False
    )
    likes: int = Field(
        ...,
        description="Количество лайков",
        example=10
    )
    dislikes: int = Field(
        ...,
        description="Количество дизлайков",
        example=2
    )
    total_rating: int = Field(
        ...,
        description="Общий рейтинг (лайки - дизлайки)",
        example=8
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания отзыва",
        example="2024-01-20T14:30:00Z"
    )
