from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, select, or_
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

    teacher_disciplines = relationship(
        "TeacherDiscipline",
        back_populates="teacher",
        cascade="all, delete-orphan"
    )

    @classmethod
    def get_joined_data(cls):
        return select(cls).options(
            selectinload(cls.teacher_disciplines)
            .joinedload(TeacherDiscipline.discipline)
            .joinedload(Discipline.module)
        ).outerjoin(TeacherDiscipline).outerjoin(Discipline).group_by(cls.id)

    @classmethod
    def apply_filters(cls, query, name_search: Optional[str] = None):
        if name_search:
            search = f"%{name_search}%"
            query = query.where(
                or_(
                    cls.first_name.ilike(search),
                    cls.surname.ilike(search),
                    cls.patronymic.ilike(search)
                )
            )
        return query

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
