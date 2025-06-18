from typing import Optional
from uuid import uuid4
from sqlalchemy import (
    Column, ForeignKey, Text, Integer, select,
    Float, Enum, Boolean, DateTime, func,
    CheckConstraint, case
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .ReviewVote import VoteTypeEnum
from models import Discipline
from database import Base
import enum


class ReviewStatusEnum(enum.Enum):
    published = "published"
    pending = "pending"
    rejected = "rejected"


class ReviewDiscipline(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    comment = Column(Text)
    grade = Column(Integer, nullable=False)
    offensive_score = Column(Float, nullable=False)
    status = Column(Enum(ReviewStatusEnum), default=ReviewStatusEnum.pending)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("grade >= 1 AND grade <= 5", name="check_grade_range"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    discipline_id = Column(UUID(as_uuid=True), ForeignKey("disciplines.id"), nullable=False)
    lector_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True
    )
    practic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True
    )

    author = relationship("User", back_populates="reviews")
    discipline = relationship("Discipline", back_populates="reviews")
    lector = relationship("Teacher", foreign_keys=[lector_id])
    practic = relationship("Teacher", foreign_keys=[practic_id])
    votes = relationship("ReviewVote", back_populates="review", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="review", cascade="all, delete-orphan")

    @classmethod
    def get_joined_data(cls):
        data = select(cls).options(
            joinedload(cls.author),
            joinedload(cls.lector),
            joinedload(cls.practic),
            joinedload(cls.discipline).joinedload(Discipline.module),
            selectinload(cls.votes),
            selectinload(cls.complaints)
        )
        return data

    @classmethod
    def apply_sorting(cls, query, sort_by: str = "date", sort_order: str = "desc"):
        from models import ReviewVote

        if sort_by == "likes":
            likes_count = func.sum(
                case(
                    (ReviewVote.vote == VoteTypeEnum.like, 1),
                    else_=0
                )
            ).label("likes_count")
            sort_expr = likes_count
        else:
            sort_expr = cls.created_at

        if sort_order.lower() == "desc":
            return query.order_by(sort_expr.desc())
        return query.order_by(sort_expr.asc())

    @classmethod
    def add_likes_count(cls, query):
        from models import ReviewVote
        from sqlalchemy import case

        return (
            query.outerjoin(ReviewVote)
            .add_columns(func.sum(case((
                ReviewVote.vote == VoteTypeEnum.like, 1),
                else_=0
            )).label("likes_count"))
            .group_by(cls.id)
        )

    @classmethod
    async def paginated_query(
            cls,
            db: AsyncSession,
            base_filters: list = None,
            current_user: Optional[dict] = None,
            page: int = 1,
            page_size: int = 40,
            sort_by: str = "date",
            sort_order: str = "desc"
    ):
        query = cls.get_joined_data()
        query = cls.add_likes_count(query)

        if base_filters:
            query = query.where(*base_filters)

        count_query = query.with_only_columns(func.count(cls.id.distinct()))
        total_result = await db.execute(count_query)
        total = total_result.unique().scalar_one_or_none() or 0

        sorted_query = cls.apply_sorting(query, sort_by, sort_order)

        paginated_query = sorted_query.limit(page_size).offset((page - 1) * page_size)

        result = await db.execute(paginated_query)
        reviews = result.unique().scalars().all()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        user_id = str(current_user["id"]) if current_user else None
        return {
            "data": [r.dto_with_user_vote_info(user_id) for r in reviews],
            "pagination": {
                "total": total,
                "total_pages": total_pages,
                "page": page,
                "size": page_size
            }
        }

    def get_dto(self):
        likes = sum(1 for v in self.votes if v.vote == VoteTypeEnum.like)
        dislikes = sum(1 for v in self.votes if v.vote == VoteTypeEnum.dislike)
        total_rating = likes - dislikes

        author_info = None
        if self.user_id and not self.is_anonymous:
            author_info = {
                "id": str(self.user_id),
                "first_name": self.author.first_name,
                "surname": self.author.surname,
                "patronymic": self.author.patronymic
                if self.author else "Unknown"
            }

        return {
            "id": str(self.id),
            "grade": self.grade,
            "comment": self.comment,
            "status": self.status.value,
            "author": author_info,
            "discipline": {
                "id": str(self.discipline.id),
                "name": self.discipline.name,
                "module": {
                    "id": str(self.discipline.module.id),
                    "name": self.discipline.module.name
                }
            },
            "lector": {
                "id": str(self.lector_id),
                "first_name": self.lector.first_name,
                "surname": self.lector.surname,
                "patronymic": self.lector.patronymic,
            } if self.lector else None,
            "practic": {
                "id": str(self.practic_id),
                "first_name": self.practic.first_name,
                "surname": self.practic.surname,
                "patronymic": self.practic.patronymic,
            } if self.practic else None,
            "offensive_score": self.offensive_score,
            "is_anonymous": self.is_anonymous,
            "likes": likes,
            "dislikes": dislikes,
            "total_rating": total_rating,
            "user_vote": None,
            "complaints_count": len(
                [complaint for complaint in self.complaints if not complaint.resolved]
            ),
            "created_at": self.created_at.isoformat(),
        }

    def dto_with_user_vote_info(self, user_id: Optional[str]):
        dto = self.get_dto()
        dto["user_vote"] = self._get_user_vote(user_id)
        return dto

    def _get_user_vote(self, user_id: Optional[str]):
        if not user_id:
            return None

        for vote in self.votes:
            if str(vote.user_id) == user_id:
                return vote.vote.value
        return None
