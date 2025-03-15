from sqlalchemy import Column, Integer, ForeignKey
from database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

