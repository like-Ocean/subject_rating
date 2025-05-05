from sqlalchemy import (
    Column, Boolean, ForeignKey, DateTime, func, select
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, joinedload, selectinload
from database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from models import Discipline, ReviewDiscipline


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved = Column(Boolean, default=False)

    review = relationship("ReviewDiscipline", back_populates="complaints")
    user = relationship("User", back_populates="complaints")

    @classmethod
    async def find_active_complaint(
        cls,
        db: AsyncSession,
        review_id: str,
        user_id: str
    ):
        result = await db.execute(
            select(cls)
            .where(
                cls.review_id == review_id,
                cls.user_id == user_id,
                cls.resolved == False
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    def get_reviews_with_pending_complaints(cls):
        return (
            select(ReviewDiscipline)
            .join(cls)
            .options(
                joinedload(ReviewDiscipline.author),
                joinedload(ReviewDiscipline.lector),
                joinedload(ReviewDiscipline.practic),
                joinedload(ReviewDiscipline.discipline).joinedload(Discipline.module),
                selectinload(ReviewDiscipline.votes),
                selectinload(ReviewDiscipline.complaints)
            )
            .where(cls.resolved == False)
            .distinct()
        )

    @classmethod
    async def get_by_review_id(cls, db: AsyncSession, review_id: str):
        result = await db.execute(
            select(cls)
            .where(
                cls.review_id == review_id,
                cls.resolved == False
            )
        )
        return result.scalars().all()
