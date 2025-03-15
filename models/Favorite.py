from uuid import uuid4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    discipline_id = Column(UUID(as_uuid=True), ForeignKey("disciplines.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="favorites")
    discipline = relationship("Discipline", back_populates="favorites")