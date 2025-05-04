from pydantic import BaseModel, UUID4, Field
from typing import Optional
from models.ReviewDiscipline import ReviewStatusEnum
from models.ReviewVote import VoteTypeEnum


class CreateReviewModel(BaseModel):
    discipline_id: UUID4
    grade: int = Field(..., description="Rating from 1 to 5")
    comment: Optional[str] = Field(..., max_length=2000)
    is_anonymous: bool = False
    lector_id: UUID4
    practic_id: UUID4


class UpdateReviewStatus(BaseModel):
    id: str = Field(..., description="review_id")
    status: ReviewStatusEnum


class AddVoteModel(BaseModel):
    id: str = Field(..., description="review_id")
    vote: VoteTypeEnum


class EditReviewModel(BaseModel):
    id: UUID4 = Field(..., description="review_id")
    grade: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)
    is_anonymous: Optional[bool] = None
    lector_id: Optional[UUID4] = None
    practic_id: Optional[UUID4] = None


class DeleteReviewModel(BaseModel):
    id: str = Field(..., description="review_id")
