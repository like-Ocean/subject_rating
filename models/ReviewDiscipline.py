from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Text, Integer, Float, Enum, Boolean, DateTime, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

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
    review_comments = relationship("ReviewComment", back_populates="review", cascade="all, delete-orphan")
