from sqlalchemy import Column, Integer, Enum
from sqlalchemy.orm import relationship

from database import Base
import enum


class RoleEnum(enum.Enum):
    user = "USER"
    admin = "ADMIN"
    super_admin = "SUPER-ADMIN"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(Enum(RoleEnum), unique=True, nullable=False)

    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
