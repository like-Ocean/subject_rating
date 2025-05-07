from pydantic import BaseModel, UUID4, Field
from typing import Optional, Literal
from models.ReviewDiscipline import ReviewStatusEnum
from models.ReviewVote import VoteTypeEnum


class ReviewIdBase(BaseModel):
    id: str = Field(..., description="review_id")


class ReviewFieldsMixin(BaseModel):
    discipline_id: Optional[UUID4] = None
    grade: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)
    is_anonymous: Optional[bool] = None
    lector_id: Optional[UUID4] = None
    practic_id: Optional[UUID4] = None


class CreateReviewModel(ReviewFieldsMixin):
    discipline_id: UUID4
    grade: int = Field(..., ge=1, le=5)
    lector_id: UUID4
    practic_id: UUID4
    comment: Optional[str] = Field(None, max_length=2000)
    is_anonymous: bool = False

    class Config:
        extra = "forbid"


class UpdateReviewStatus(ReviewIdBase):
    status: ReviewStatusEnum


class AddVoteModel(ReviewIdBase):
    vote: VoteTypeEnum


class EditReviewModel(ReviewFieldsMixin):
    id: UUID4 = Field(..., description="review_id")


class DeleteReviewModel(ReviewIdBase):
    pass


class CreateComplaintModel(ReviewIdBase):
    pass


class ResolveComplaintModel(ReviewIdBase):
    action: Literal["delete", "dismiss"] = Field(..., description="delete or dismiss")
