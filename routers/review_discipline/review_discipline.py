from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from service import review_discipline_service, user_service
from models import User
from models.ReviewDiscipline import ReviewStatusEnum
from database import get_db
from .review_discipline_scheme import (
    CreateReviewModel, UpdateReviewStatus,
    AddVoteModel, DeleteReviewModel, EditReviewModel
)
from response_models import ReviewResponse


review_router = APIRouter(prefix="/reviews", tags=["reviews"])


@review_router.post("/add", response_model=ReviewResponse)
async def create_review(
    data: CreateReviewModel,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    review = await review_discipline_service.create_review(
        db, current_user, data.discipline_id, data.grade,
        data.comment, data.is_anonymous, data.lector_id, data.practic_id
    )
    return review


@review_router.patch("/review/edit", response_model=ReviewResponse)
async def edit_review(
    data: EditReviewModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await review_discipline_service.edit_review(
        db, current_user, data.id, data.grade, data.comment, data.is_anonymous,
        data.lector_id, data.practic_id
    )


@review_router.delete("/review/delete")
async def delete_review(
    data: DeleteReviewModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await review_discipline_service.delete_review(
        db, current_user, data.id
    )


@review_router.get("", response_model=List[ReviewResponse])
async def get_reviews(
    db: AsyncSession = Depends(get_db),
    discipline_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(40)
):
    return await review_discipline_service.get_all_reviews(
        db, discipline_id, page, page_size
    )


@review_router.get("/review/admin/moderation", response_model=List[ReviewResponse])
async def get_moderation_reviews(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(user_service.get_current_user),
        status: ReviewStatusEnum = Query(ReviewStatusEnum.pending),
        page: int = Query(1, ge=1),
        page_size: int = Query(40),
):
    return await review_discipline_service.get_reviews_by_status(
        db, current_user, status, page, page_size
    )


@review_router.patch("/review/admin/status/edit", response_model=ReviewResponse)
async def change_review_status(
    data: UpdateReviewStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    return await review_discipline_service.update_review_status(
        db, data.id, data.status, current_user
    )


@review_router.post("/review/vote", response_model=ReviewResponse)
async def add_vote(
        data: AddVoteModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await review_discipline_service.vote_review(
        db, data.id, current_user, data.vote
    )


@review_router.get("/my", response_model=List[ReviewResponse])
async def get_my_reviews(
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(40),

):
    return await review_discipline_service.get_my_reviews(
        db, current_user, page, page_size
    )
