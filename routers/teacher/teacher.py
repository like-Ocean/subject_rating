from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from service import teacher_service
from models import User
from database import get_db
from service import user_service
from response_models import TeacherResponse, PaginatedResponse
from .teacher_scheme import (
    CreateTeacherModel, UpdateTeacherModel, DeleteTeacherModel,
    AppointTeacherDisciplines, RemoveTeacherDiscipline
)

teacher_router = APIRouter(prefix="/teachers", tags=["teachers"])


@teacher_router.post("/admin/teacher/create", response_model=TeacherResponse)
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


@teacher_router.patch("/admin/teacher/update", response_model=TeacherResponse)
async def update_teacher(
        data: UpdateTeacherModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    updated_teacher = await teacher_service.edit_teacher(
        db, current_user, data.id, data.first_name,
        data.surname, data.patronymic
    )
    return updated_teacher


@teacher_router.delete("/admin/teacher/delete")
async def delete_teacher(
        data: DeleteTeacherModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await teacher_service.delete_teacher(db, current_user, data.id)
    return result


@teacher_router.get("/get", response_model=PaginatedResponse[TeacherResponse])
async def get_teachers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    name_search: Optional[str] = Query(None),
    sort_field: str = Query(
        "surname",
        description="Поле для сортировки (surname, first_name)"
    ),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db)
):
    return await teacher_service.get_teachers(
        db, page, size, name_search,
        sort_field, sort_order
    )


@teacher_router.get(
    "/discipline/{id}/get-by-discipline",
    response_model=PaginatedResponse[TeacherResponse]
)
async def get_teachers_by_discipline(
    id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    name_search: Optional[str] = Query(None),
    sort_field: str = Query("surname", description="Поле для сортировки"),
    sort_order: str = Query("asc", description="Порядок сортировки"),
    db: AsyncSession = Depends(get_db)
):
    return await teacher_service.get_teachers_by_discipline(
        db=db, discipline_id=id, page=page, size=size,
        name_search=name_search, sort_field=sort_field,
        sort_order=sort_order
    )


@teacher_router.post("/admin/teacher/discipline/appoint", response_model=TeacherResponse)
async def appoint_teacher_discipline(
        data: AppointTeacherDisciplines,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await teacher_service.appoint_teacher_disciplines(
        db, current_user, data.id,
        [str(disc_id) for disc_id in data.discipline_ids]
    )
    return teacher


@teacher_router.delete("/admin/teacher/discipline/remove", response_model=TeacherResponse)
async def remove_teacher_discipline(
        data: RemoveTeacherDiscipline,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await teacher_service.remove_teacher_discipline(
        db, current_user, data.id, data.discipline_id
    )
    return teacher
