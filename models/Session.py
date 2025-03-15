from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    user = relationship("User", back_populates="sessions")
