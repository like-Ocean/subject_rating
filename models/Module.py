import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Module(Base):
    __tablename__ = "modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    disciplines = relationship("Discipline", back_populates="module")
