from pydantic import BaseModel, UUID4, Field
from typing import Optional


class CreateReviewModel(BaseModel):
    discipline_id: UUID4
    grade: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=2000)
    is_anonymous: bool = False
    lector_id: UUID4
    practic_id: UUID4
