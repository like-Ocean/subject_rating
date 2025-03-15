from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)

    author = relationship("User", back_populates="comments")
    review = relationship("ReviewDiscipline", back_populates="review_comments")