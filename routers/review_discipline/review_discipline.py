from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from service import review_discipline_service, user_service
from models import User
from models.ReviewDiscipline import ReviewStatusEnum
from database import get_db
from .review_discipline_scheme import CreateReviewModel, UpdateReviewStatus


review_router = APIRouter(prefix="/review", tags=["reviews"])


@review_router.get("")
async def get_reviews(
    db: AsyncSession = Depends(get_db),
    discipline_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(40)
):
    return await review_discipline_service.get_all_reviews(
        db, discipline_id, page, page_size
    )


@review_router.post("/add")
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


@review_router.patch("/{review_id}/status")
async def change_review_status(
    review_id: str,
    data: UpdateReviewStatus,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(user_service.get_current_user)
):
    return await review_discipline_service.update_review_status(
        db, review_id, data.new_status, current_user
    )


@review_router.get("/admin/moderation")
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



