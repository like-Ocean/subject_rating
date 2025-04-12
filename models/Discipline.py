from sqlalchemy import Column, String, Text, Enum, ForeignKey, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, selectinload
from database import Base
from uuid import uuid4
import enum


class DisciplineFormatEnum(enum.Enum):
    online = "онлайн"
    traditional = "традиционный"
    mixed = "смешанный"


class Discipline(Base):
    __tablename__ = "disciplines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(150), nullable=False)
    format = Column(Enum(DisciplineFormatEnum), nullable=False)
    description = Column(Text, nullable=True)
    modeus_link = Column(String(200), nullable=True)
    presentation_link = Column(String(200), nullable=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)

    module = relationship("Module", back_populates="disciplines")
    reviews = relationship("ReviewDiscipline", back_populates="discipline")
    favorites = relationship("Favorite", back_populates="discipline", cascade="all, delete-orphan")
    teacher_disciplines = relationship("TeacherDiscipline", back_populates="discipline")

    @classmethod
    def get_joined_data(cls):
        return select(cls).options(
            selectinload(cls.reviews),
            selectinload(cls.favorites),
            selectinload(cls.module)
        )

    def get_dto(self):
        reviews_grades = [r.grade for r in self.reviews if r.grade is not None]
        avg_rating = sum(reviews_grades) / len(reviews_grades) if reviews_grades else 0.0
        review_count = len(reviews_grades)
        favorites_count = len(self.favorites) if self.favorites else 0

        module_data = {
            "id": str(self.module.id),
            "name": self.module.name
        } if self.module else None

        return {
            "id": str(self.id),
            "name": self.name,
            "format": self.format.value if self.format else None,
            "description": self.description,
            "modeus_link": self.modeus_link,
            "presentation_link": self.presentation_link,
            "module": module_data,
            "avg_rating": round(avg_rating, 1),
            "review_count": review_count,
            "favorites_count": favorites_count
        }
