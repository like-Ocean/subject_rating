from uuid import uuid4
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    patronymic = Column(String(50), nullable=True)

    teacher_disciplines = relationship("TeacherDiscipline", back_populates="teacher")
