from uuid import uuid4
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    patronymic = Column(String(50), nullable=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    is_block = Column(Boolean, default=False)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("ReviewDiscipline", back_populates="author")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("ReviewComment", back_populates="author", cascade="all, delete-orphan")
    votes = relationship("ReviewVote", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password, password)
