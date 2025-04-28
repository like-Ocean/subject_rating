from typing import Optional
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from check_swear import SwearingCheck
from models import (
    Discipline, ReviewDiscipline, ReviewVote, ReviewStatusEnum,
    DisciplineFormatEnum, User, Teacher, TeacherDiscipline
)

swear_checker = SwearingCheck()


def get_review_status(offensive_score: float) -> ReviewStatusEnum:
    if offensive_score >= 0.99:
        return ReviewStatusEnum.rejected
    if offensive_score >= 0.50:
        return ReviewStatusEnum.pending
    return ReviewStatusEnum.published


# (если проверка выдала 1 и пользователь не авторизован, отзыв сохранять или нет?)
async def create_review(
        db: AsyncSession, current_user: Optional[User],
        discipline_id: str, grade: int, comment: str,
        is_anonymous: bool, lector_id: str, practic_id: str
):
    discipline = await db.get(Discipline, discipline_id)
    if not discipline:
        raise HTTPException(404, "Discipline not found")

    lector = await db.get(Teacher, lector_id)
    practic = await db.get(Teacher, practic_id)
    if not lector or not practic:
        raise HTTPException(404, "Teacher not found")

    if not await TeacherDiscipline.exists_assignment(db, lector_id, discipline_id):
        raise HTTPException(
            status_code=400,
            detail="Lector is not assigned to this discipline"
        )

    if not await TeacherDiscipline.exists_assignment(db, practic_id, discipline_id):
        raise HTTPException(
            status_code=400,
            detail="Practic teacher is not assigned to this discipline"
        )

    offensive_score = 0.0
    if comment:
        try:
            raw_score = swear_checker.predict_proba([comment])[0]
        except Exception:
            raise HTTPException(status_code=500, detail="Content analysis failed")
        offensive_score = round(raw_score, 4)

    status = get_review_status(offensive_score)

    user_id = None
    final_anonymous = True
    if current_user:
        user_id = current_user["id"]
        final_anonymous = is_anonymous

    new_review = ReviewDiscipline(
        user_id=user_id,
        discipline_id=discipline_id,
        lector_id=lector_id,
        practic_id=practic_id,
        grade=grade,
        comment=comment,
        offensive_score=offensive_score,
        status=status,
        is_anonymous=final_anonymous
    )

    try:
        db.add(new_review)
        await db.commit()
        await db.refresh(new_review)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Invalid data format")

    result = await db.execute(
        ReviewDiscipline.get_joined_data()
        .where(ReviewDiscipline.id == new_review.id)
    )
    refreshed = result.scalars().first()

    return refreshed.get_dto()


# получился хайп, узнать как для фронта удобней 1 роут с опцией или 2 разных роута
# TODO: сделать пагинацию и page_size на всех get запросах. Написать функционал отправки
#  письма на почту если забыл пароль
async def get_all_reviews(
        db: AsyncSession,
        discipline_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 40
):
    query = ReviewDiscipline.get_joined_data().where(
        ReviewDiscipline.status == ReviewStatusEnum.published
    )

    if discipline_id:
        query = query.where(ReviewDiscipline.discipline_id == discipline_id)

    result = await db.execute(
        query.order_by(ReviewDiscipline.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return [review.get_dto() for review in result.unique().scalars().all()]


async def get_reviews_by_status(
        db: AsyncSession,
        current_user: User,
        status: ReviewStatusEnum,
        page: int = 1,
        page_size: int = 20
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can get reviews by status"
        )

    result = await db.execute(
        ReviewDiscipline.get_joined_data()
        .where(ReviewDiscipline.status == status)
        .order_by(ReviewDiscipline.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return [review.get_dto() for review in result.unique().scalars().all()]


async def update_review_status(
        db: AsyncSession,
        review_id: str,
        new_status: ReviewStatusEnum,
        current_user: User
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can update status")

    result = await db.execute(
        ReviewDiscipline.get_joined_data()
        .where(ReviewDiscipline.id == review_id)
    )
    review = result.unique().scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")

    review.status = new_status
    try:
        await db.commit()
        await db.refresh(review)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Invalid status transition")

    return review.get_dto()
