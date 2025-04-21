from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from service import review_discipline_service, user_service
from models import User
from database import get_db
from .review_discipline_scheme import CreateReviewModel


review_discipline_router = APIRouter(prefix="/review", tags=["reviews"])


@review_discipline_router.post("/add")
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



