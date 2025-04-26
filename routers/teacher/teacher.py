from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from service import teacher_service
from models import User
from database import get_db
from service import user_service
from .teacher_scheme import (
    CreateTeacherModel, UpdateTeacherModel, DeleteTeacherModel,
    AppointTeacherDisciplines, RemoveTeacherDiscipline
)


teacher_router = APIRouter(prefix="/teachers", tags=["teachers"])


@teacher_router.post("/admin/teacher/create")
async def create_teacher(
        data: CreateTeacherModel,
        current_user: dict = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await teacher_service.create_teacher(
        db, current_user, data.first_name,
        data.surname, data.patronymic
    )
    return teacher


@teacher_router.patch("/admin/teacher/update")
async def update_teacher(
    data: UpdateTeacherModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_teacher = await teacher_service.edit_teacher(
        db, current_user, data.teacher_id, data.first_name,
        data.surname, data.patronymic
    )
    return updated_teacher


@teacher_router.delete("/admin/teacher/delete")
async def delete_teacher(
    data: DeleteTeacherModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await teacher_service.delete_teacher(db, current_user, data.teacher_id, )
    return result


@teacher_router.get("/get")
async def get_teachers(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_teachers(db)
    return teachers


@teacher_router.get("/{discipline_id}/get-by-discipline")
async def get_teachers_by_discipline(
    discipline_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await teacher_service.get_teachers_by_discipline(db, discipline_id)


@teacher_router.post("/admin/teacher/discipline/appoint")
async def appoint_teacher_discipline(
        data: AppointTeacherDisciplines,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await teacher_service.appoint_teacher_disciplines(
        db, current_user, data.teacher_id,
        [str(disc_id) for disc_id in data.discipline_ids]
    )
    return teacher


@teacher_router.delete("/admin/teacher/discipline/remove")
async def remove_teacher_discipline(
        data: RemoveTeacherDiscipline,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await teacher_service.remove_teacher_discipline(
        db, current_user, data.teacher_id, data.discipline_id
    )
    return teacher
