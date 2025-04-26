from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from database import get_db
from service import admin_service, user_service
from .admin_scheme import (
    AddAdminModel, AddModuleModel, UpdateModuleModel,
    RemoveAdminModel, DeleteModuleModel
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


@admin_router.patch("/remove")
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


@admin_router.get("/public/modules/get")
async def get_modules(db: AsyncSession = Depends(get_db)):
    module = await admin_service.get_modules(db)
    return module
