from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from service import discipline_service
from models import User
from database import get_db
from .discipline_scheme import CreateDisciplineModel, UpdateDisciplineModel, DeleteDisciplineModel
from service import user_service


discipline_router = APIRouter(prefix="/discipline", tags=["disciplines"])


@discipline_router.post("/create")
async def create_discipline(
        data: CreateDisciplineModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    discipline = await discipline_service.create_discipline(
        db, current_user, data.name, data.format,
        data.module_id, data.description, data.modeus_link,
        data.presentation_link
    )
    return discipline


@discipline_router.patch("/update")
async def update_discipline(
        data: UpdateDisciplineModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    discipline = await discipline_service.update_discipline(
        db, current_user, data.discipline_id, data.name,
        data.format_value, data.module_id, data.description,
        data.modeus_link, data.presentation_link
    )
    return discipline


@discipline_router.delete("/delete")
async def delete_discipline(
    data: DeleteDisciplineModel,
    current_user: dict = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await discipline_service.delete_discipline(db, current_user, data.discipline_id,)
    return result


@discipline_router.get("/disciplines/get")
async def get_disciplines(db: AsyncSession = Depends(get_db)):
    disciplines = await discipline_service.get_disciplines(db)
    return disciplines


@discipline_router.get("/{discipline_id}")
async def get_discipline(discipline_id, db: AsyncSession = Depends(get_db)):
    discipline = await discipline_service.get_discipline(db, discipline_id)
    return discipline
