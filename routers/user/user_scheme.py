from pydantic import BaseModel, Field, EmailStr


class RegisterModel(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1)
    surname: str = Field(..., min_length=1)
    patronymic: str = Field(...)
    password: str = Field(..., min_length=8)


class Authorization(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
