from uuid import uuid4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class TeacherDiscipline(Base):
    __tablename__ = "teacher_disciplines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False)
    discipline_id = Column(UUID(as_uuid=True), ForeignKey("disciplines.id"), nullable=False)

    teacher = relationship("Teacher", back_populates="teacher_disciplines")
    discipline = relationship("Discipline", back_populates="teacher_disciplines")