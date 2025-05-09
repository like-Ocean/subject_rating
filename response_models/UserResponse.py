from pydantic import BaseModel, UUID4, EmailStr, Field
from typing import Optional
from models.Role import RoleEnum


class UserResponse(BaseModel):
    id: UUID4 = Field(
        ...,
        description="User ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    first_name: str = Field(
        ...,
        description="User's first name",
        example="Иван"
    )
    surname: str = Field(
        ...,
        description="User's surname",
        example="Иванов"
    )
    patronymic: Optional[str] = Field(
        None,
        description="User's patronymic",
        example="Иванович"
    )
    email: EmailStr = Field(
        ...,
        description="User's email",
        example="user@example.com"
    )
    role: RoleEnum = Field(..., description="User role", example="USER")
