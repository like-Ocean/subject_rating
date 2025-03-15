from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base
import enum


class VoteTypeEnum(enum.Enum):
    like = "like"
    dislike = "dislike"


class ReviewVote(Base):
    __tablename__ = "review_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    vote = Column(Enum(VoteTypeEnum), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)

    user = relationship("User", back_populates="votes")
    review = relationship("ReviewDiscipline", back_populates="votes")