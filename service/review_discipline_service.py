from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from check_swear import SwearingCheck
from models import (
    Discipline, ReviewDiscipline, ReviewVote, ReviewStatusEnum,
    DisciplineFormatEnum, User, Teacher
)

swear_checker = SwearingCheck()


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

    offensive_score = 0.0
    if comment:
        try:
            offensive_score = swear_checker.predict_proba([comment])[0]
        except Exception as e:
            raise HTTPException(500, "Content analysis failed")

    status = ReviewStatusEnum.published
    user_id = None
    final_anonymous = True

    if current_user:
        user_id = current_user["id"]
        final_anonymous = is_anonymous
        if offensive_score >= 0.5:
            status = ReviewStatusEnum.pending
    else:
        if offensive_score >= 0.5:
            status = ReviewStatusEnum.pending

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

    refreshed = (
        await db.execute(ReviewDiscipline.get_joined_data())
    ).scalars().first()

    return refreshed.get_dto()
