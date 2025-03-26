from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

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

    def get_dto(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "format": self.format,
            "description": self.description,
            "modeus_link": self.modeus_link,
            "presentation_link": self.presentation_link,
            "module_id": self.module_id
        }