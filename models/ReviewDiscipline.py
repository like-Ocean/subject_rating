from uuid import uuid4
from sqlalchemy import (
    Column, ForeignKey, Text, Integer, select,
    Float, Enum, Boolean, DateTime, func, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, joinedload, selectinload
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
    lector_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False)
    practic_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False)

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
        sort_mapping = {
            "date": cls.created_at,
            "likes": "likes_count"
        }
        sort_column = sort_mapping.get(sort_by, cls.created_at)

        if sort_order.lower() == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()

        return query.order_by(sort_column)

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
            "complaints_count": len(
                [complaint for complaint in self.complaints if not complaint.resolved]
            ),
            "created_at": self.created_at.isoformat(),
        }
