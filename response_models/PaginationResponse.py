from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    total: int = Field(...)
    total_pages: int = Field(...)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T] = Field(...)
    pagination: Pagination = Field(...)
