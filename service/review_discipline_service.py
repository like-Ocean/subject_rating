from typing import Optional
from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from check_swear import SwearingCheck
from models import (
    Discipline, ReviewDiscipline, ReviewVote, ReviewStatusEnum,
    Complaint, User, Teacher, TeacherDiscipline, VoteTypeEnum
)

swear_checker = SwearingCheck()


def get_review_status(offensive_score: float) -> ReviewStatusEnum:
    if offensive_score >= 0.80:
        return ReviewStatusEnum.rejected
    if offensive_score >= 0.50:
        return ReviewStatusEnum.pending
    return ReviewStatusEnum.published


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
            raise HTTPException(
                status_code=500,
                detail="Content analysis failed"
            )
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


async def edit_review(
        db: AsyncSession,
        current_user: User,
        review_id: str,
        new_grade: Optional[int] = None,
        new_comment: Optional[str] = None,
        new_is_anonymous: Optional[bool] = None,
        new_lector_id: Optional[str] = None,
        new_practic_id: Optional[str] = None
):
    result = await db.execute(
        ReviewDiscipline.get_joined_data()
        .where(ReviewDiscipline.id == review_id)
    )
    review = result.unique().scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if not review.user_id or str(review.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    if new_lector_id or new_practic_id:
        discipline_id = review.discipline_id
        if new_lector_id:
            if not await TeacherDiscipline.exists_assignment(
                    db, new_lector_id, discipline_id
            ):
                raise HTTPException(
                    400,
                    "New lector not assigned to discipline"
                )
            review.lector_id = new_lector_id

        if new_practic_id:
            if not await TeacherDiscipline.exists_assignment(
                    db, new_practic_id, discipline_id
            ):
                raise HTTPException(
                    400,
                    "New practic teacher not assigned to discipline"
                )
            review.practic_id = new_practic_id

    if new_grade is not None:
        review.grade = new_grade
    if new_comment is not None:
        review.comment = new_comment
    if new_is_anonymous is not None:
        review.is_anonymous = new_is_anonymous

    if new_comment is not None:
        try:
            raw_score = swear_checker.predict_proba([new_comment])[0]
        except Exception:
            raise HTTPException(500, "Content analysis failed")
        review.offensive_score = round(raw_score, 4)
        review.status = get_review_status(review.offensive_score)

    try:
        await db.commit()
        await db.refresh(review)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(400, "Invalid data format")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")

    return review.get_dto()


async def delete_review(db: AsyncSession, current_user: User, review_id: str):
    result = await db.execute(
        ReviewDiscipline.get_joined_data()
        .where(ReviewDiscipline.id == review_id)
    )
    review = result.unique().scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    is_author = str(review.user_id) == current_user["id"] if review.user_id else False
    is_admin = "ADMIN" in current_user.get("roles", [])
    is_super_admin = "SUPER-ADMIN" in current_user.get("roles", [])

    if not (is_author or is_admin or is_super_admin):
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        await db.delete(review)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return Response(status_code=200)


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
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can update status"
        )

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


async def vote_review(
        db: AsyncSession,
        review_id: str,
        current_user: User,
        vote: VoteTypeEnum
):
    review_result = await db.execute(
        ReviewDiscipline.get_joined_data()
        .where(ReviewDiscipline.id == review_id)
    )
    review = review_result.unique().scalar_one_or_none()
    if not review:
        raise HTTPException(404, "Review not found")

    existing_vote = next(
        (vote for vote in review.votes if str(vote.user_id) == current_user["id"]),
        None
    )

    if existing_vote:
        if existing_vote.vote == vote:
            await db.delete(existing_vote)
        else:
            existing_vote.vote = vote
    else:
        new_vote = ReviewVote(
            review_id=review_id,
            user_id=current_user["id"],
            vote=vote
        )
        db.add(new_vote)

    try:
        await db.commit()
        await db.refresh(review)
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, "Failed to process vote")

    return review.get_dto()


async def get_my_reviews(
        db: AsyncSession,
        current_user: User,
        page: int = 1,
        page_size: int = 40
):
    query = ReviewDiscipline.get_joined_data().where(
        ReviewDiscipline.user_id == current_user["id"]
    )
    result = await db.execute(
        query.order_by(ReviewDiscipline.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    return [review.get_dto() for review in result.unique().scalars().all()]


async def create_complaint(
        db: AsyncSession,
        current_user: User,
        review_id: str
):
    review = await db.get(ReviewDiscipline, review_id)
    if not review:
        raise HTTPException(404, "Review not found")

    if review.user_id and str(review.user_id) == current_user["id"]:
        raise HTTPException(400, "Cannot complain on own review")

    existing_complaint = await Complaint.find_active_complaint(
        db, review_id, current_user["id"]
    )
    if existing_complaint:
        raise HTTPException(400, "Complaint already exists")

    new_complaint = Complaint(
        review_id=review_id,
        user_id=current_user["id"]
    )
    db.add(new_complaint)

    try:
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(500, "Database error")

    return {"message": "Complaint sent successfully"}


async def get_pending_complaints(
        db: AsyncSession,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can access this resource"
        )

    query = Complaint.get_reviews_with_pending_complaints()
    paginated_query = (
        query.order_by(ReviewDiscipline.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    result = await db.execute(paginated_query)
    reviews = result.unique().scalars().all()

    return [review.get_dto() for review in reviews]


async def resolve_complaint(
    db: AsyncSession,
    current_user: User,
    review_id: str,
    action: str
):
    if not ("ADMIN" in current_user.get("roles", []) or "SUPER-ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can resolve complaints"
        )

    complaints = await Complaint.get_by_review_id(db, review_id)
    if not complaints:
        raise HTTPException(
            404,
            "No active complaints found for this review"
        )

    review = await db.get(ReviewDiscipline, review_id)
    if not review:
        raise HTTPException(404, "Review not found")

    if action == "delete":
        await db.delete(review)
    elif action == "dismiss":
        for complaint in complaints:
            complaint.resolved = True
    else:
        raise HTTPException(
            400,
            "Invalid action. Allowed: 'delete' or 'dismiss'"
        )

    try:
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")

    return {"message": "Complaint resolved successfully"}
