from uuid import uuid4
from sqlalchemy import Column, String, or_
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

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("ReviewDiscipline", back_populates="author")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    votes = relationship("ReviewVote", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    complaints = relationship("Complaint", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password, password)

    @classmethod
    def apply_search_filter(cls, query, search_term: str):
        return query.where(
            or_(
                cls.first_name.ilike(f"%{search_term}%"),
                cls.surname.ilike(f"%{search_term}%"),
                cls.patronymic.ilike(f"%{search_term}%")
            )
        )

    @classmethod
    def apply_sorting(cls, query, sort_field: str = "surname", sort_order: str = "asc"):
        sort_mapping = {
            "surname": cls.surname,
            "first_name": cls.first_name
        }

        sort_column = sort_mapping.get(sort_field, cls.surname)
        if sort_order.lower() == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()

        return query.order_by(sort_column)

    def get_dto(self):
        if self.user_roles:
            role = self.user_roles[0].role.name.value
        else:
            role = None

        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "surname": self.surname,
            "patronymic": self.patronymic,
            "email": self.email,
            "role": role
        }

