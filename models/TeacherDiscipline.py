from uuid import uuid4
from sqlalchemy import Column, ForeignKey, select, exists
from sqlalchemy.ext.asyncio import AsyncSession
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

    @classmethod
    async def exists_assignment(
            cls,
            db: AsyncSession,
            teacher_id: str,
            discipline_id: str
    ) -> bool:
        stmt = select(exists().where(
            cls.teacher_id == teacher_id,
            cls.discipline_id == discipline_id
        ))
        return (await db.execute(stmt)).scalar()
