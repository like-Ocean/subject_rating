from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from response_models import UserResponse, ModuleResponse
from models import User
from database import get_db
from service import admin_service, user_service
from .admin_scheme import (
    AddAdminModel, AddModuleModel, UpdateModuleModel,
    DeleteModuleModel
)

admin_router = APIRouter(prefix="/admin", tags=["admins"])


@admin_router.patch("/add", response_model=UserResponse)
async def appoint_admin(
    data: AddAdminModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await admin_service.appoint_admin(
        data.id, current_user, db
    )
    return updated_user


@admin_router.patch("/remove", response_model=UserResponse)
async def remove_admin(
    data: AddAdminModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_user = await admin_service.remove_admin(
        data.id, current_user, db
    )
    return updated_user


@admin_router.post("/module/add", response_model=ModuleResponse)
async def add_module(
    data: AddModuleModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    module = await admin_service.add_module(data.name, current_user, db)
    return module


@admin_router.patch("/module/update", response_model=ModuleResponse)
async def update_module(
    data: UpdateModuleModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated_module = await admin_service.update_module(
        data.id,
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
        data.id,
        current_user,
        db
    )
    return result


@admin_router.get("/public/modules/get", response_model=List[ModuleResponse])
async def get_modules(db: AsyncSession = Depends(get_db)):
    module = await admin_service.get_modules(db)
    return module
