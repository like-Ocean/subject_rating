from uuid import uuid4
from sqlalchemy import Column, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, selectinload
from .TeacherDiscipline import TeacherDiscipline
from .Discipline import Discipline
from database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    patronymic = Column(String(50), nullable=True)

    teacher_disciplines = relationship("TeacherDiscipline", back_populates="teacher")

    @classmethod
    def get_joined_data(cls):
        return select(cls).options(
            selectinload(cls.teacher_disciplines)
            .joinedload(TeacherDiscipline.discipline)
            .joinedload(Discipline.module)
        )

    def get_dto(self):
        disciplines = []
        for td in self.teacher_disciplines:
            if td.discipline and td.discipline.module:
                disciplines.append({
                    "id": str(td.discipline.id),
                    "name": td.discipline.name,
                    "module": {
                        "id": str(td.discipline.module.id),
                        "name": td.discipline.module.name
                    }
                })

        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "surname": self.surname,
            "patronymic": self.patronymic,
            "disciplines": disciplines
        }
