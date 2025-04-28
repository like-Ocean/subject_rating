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


class ChangeModel(BaseModel):
    id: str = Field(..., description="user_id")
    first_name: str | None = Field(None)
    surname: str | None = Field(None)
    patronymic: str | None = Field(None)
    email: EmailStr | None = Field(None)


class ChangePasswordModel(BaseModel):
    id: str = Field(..., description="user_id")
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
