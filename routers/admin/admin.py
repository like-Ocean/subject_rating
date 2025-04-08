from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from database import get_db
from service import admin_service, user_service
from .admin_scheme import (
    AddAdminModel, AddModuleModel, UpdateModuleModel,
    RemoveAdminModel, DeleteModuleModel, CreateTeacherModel, UpdateTeacherModel,
    DeleteTeacherModel, CreateDisciplineModel, UpdateDisciplineModel, DeleteDisciplineModel,
    AppointTeacherDiscipline
)

admin_router = APIRouter(prefix="/admin", tags=["admins"])


@admin_router.patch("/add")
async def appoint_admin(
    data: AddAdminModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await admin_service.appoint_admin(
        data.target_user_id, current_user, db
    )
    return updated_user


@admin_router.patch("/admin/remove")
async def remove_admin(
    data: RemoveAdminModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await admin_service.remove_admin(
        data.target_user_id, current_user, db
    )
    return updated_user


@admin_router.post("/module/add")
async def add_module(
    data: AddModuleModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    module = await admin_service.add_module(data.name, current_user, db)
    return module


@admin_router.patch("/module/update")
async def update_module(
    data: UpdateModuleModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_module = await admin_service.update_module(
        data.module_id,
        data.new_name,
        current_user,
        db
    )
    return updated_module


@admin_router.delete("/module/delete")
async def delete_module(
    data: DeleteModuleModel,
    current_user: dict = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await admin_service.delete_module(
        data.module_id,
        current_user,
        db
    )
    return result


@admin_router.get("/modules/get")
async def get_modules(db: AsyncSession = Depends(get_db)):
    module = await admin_service.get_modules(db)
    return module


@admin_router.post("/teacher/create")
async def create_teacher(
        data: CreateTeacherModel,
        current_user: dict = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await admin_service.create_teacher(
        db, current_user, data.first_name,
        data.surname, data.patronymic
    )
    return teacher


@admin_router.patch("/teacher/update")
async def update_teacher(
    data: UpdateTeacherModel,
    current_user: dict = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_teacher = await admin_service.edit_teacher(
        db, current_user, data.teacher_id, data.first_name,
        data.surname, data.patronymic
    )
    return updated_teacher


@admin_router.delete("/teacher/delete")
async def delete_teacher(
    data: DeleteTeacherModel,
    current_user: dict = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await admin_service.delete_teacher(db, current_user, data.teacher_id,)
    return result


@admin_router.get("/teachers/get")
async def get_teachers(db: AsyncSession = Depends(get_db)):
    teachers = await admin_service.get_teachers(db)
    return teachers


@admin_router.post("/discipline/create")
async def create_discipline(
        data: CreateDisciplineModel,
        current_user: dict = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    discipline = await admin_service.create_discipline(
        db, current_user, data.name, data.format,
        data.module_id, data.description, data.modeus_link,
        data.presentation_link
    )
    return discipline


@admin_router.patch("/discipline/update")
async def update_discipline(
        data: UpdateDisciplineModel,
        current_user: dict = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    discipline = await admin_service.update_discipline(
        db, current_user, data.discipline_id, data.name,
        data.format_value, data.module_id, data.description,
        data.modeus_link, data.presentation_link
    )
    return discipline


@admin_router.delete("/discipline/delete")
async def delete_discipline(
    data: DeleteDisciplineModel,
    current_user: dict = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await admin_service.delete_teacher(db, current_user, data.discipline_id,)
    return result


@admin_router.get("/disciplines/get")
async def get_disciplines(db: AsyncSession = Depends(get_db)):
    disciplines = await admin_service.get_disciplines(db)
    return disciplines


@admin_router.post("/teacher/discipline/appoint")
async def appoint_teacher_discipline(
        data: AppointTeacherDiscipline,
        current_user: dict = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await admin_service.appoint_teacher_discipline(
        db, current_user, data.teacher_id, data.discipline_id
    )
    return teacher


@admin_router.delete("/teacher/discipline/remove")
async def remove_teacher_discipline(
        data: AppointTeacherDiscipline,
        current_user: dict = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    teacher = await admin_service.remove_teacher_discipline(
        db, current_user, data.teacher_id, data.discipline_id
    )
    return teacher
