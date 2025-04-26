from pydantic import BaseModel, UUID4, Field
from typing import Optional
from models.ReviewDiscipline import ReviewStatusEnum


class CreateReviewModel(BaseModel):
    discipline_id: UUID4
    grade: int = Field(..., description="Rating from 1 to 5")
    comment: Optional[str] = Field(..., max_length=2000)
    is_anonymous: bool = False
    lector_id: UUID4
    practic_id: UUID4


class UpdateReviewStatus(BaseModel):
    new_status: ReviewStatusEnum
