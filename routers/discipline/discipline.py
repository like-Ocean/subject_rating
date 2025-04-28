from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from service import discipline_service
from models import User, DisciplineFormatEnum
from database import get_db
from response_models import DisciplineResponse
from .discipline_scheme import (
    CreateDisciplineModel, UpdateDisciplineModel,
    DeleteDisciplineModel, AddFavorite, SortOrder,
    SortBy
)
from service import user_service


discipline_router = APIRouter(prefix="/disciplines", tags=["disciplines"])


@discipline_router.post("/admin/discipline/create", response_model=DisciplineResponse)
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


@discipline_router.patch("/admin/discipline/update", response_model=DisciplineResponse)
async def update_discipline(
        data: UpdateDisciplineModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    discipline = await discipline_service.update_discipline(
        db, current_user, data.id, data.name,
        data.format, data.module_id, data.description,
        data.modeus_link, data.presentation_link
    )
    return discipline


@discipline_router.delete("/admin/discipline/delete")
async def delete_discipline(
    data: DeleteDisciplineModel,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await discipline_service.delete_discipline(db, current_user, data.id,)
    return result


@discipline_router.get("/get", response_model=List[DisciplineResponse])
async def get_disciplines(db: AsyncSession = Depends(get_db)):
    return await discipline_service.get_disciplines(db)


@discipline_router.get("/search", response_model=List[DisciplineResponse])
async def search_disciplines(
    db: AsyncSession = Depends(get_db),
    name_search: Optional[str] = Query(
        None,
        description="Поиск по названию дисциплины"
    ),
    module_search: Optional[str] = Query(
        None,
        description="Поиск по названию модуля"
    ),
    format_filter: Optional[DisciplineFormatEnum] = Query(
        None,
        description="Фильтр по формату дисциплины"
    ),
    sort_by: SortBy = Query(
        SortBy.rating,
        description="Сортировать по"
    ),
    sort_order: SortOrder = Query(
        SortOrder.desc,
        description="Порядок сортировки"
    )
):
    return await discipline_service.search_disciplines(
        db,name_search,module_search,
        format_filter.value if format_filter else None,
        sort_by.value,
        sort_order.value
    )


@discipline_router.get("/discipline/{id}", response_model=DisciplineResponse)
async def get_discipline(id, db: AsyncSession = Depends(get_db)):
    return await discipline_service.get_discipline(db, id)


@discipline_router.post("/favorite/add", response_model=DisciplineResponse)
async def add_favorite(
    data: AddFavorite,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await discipline_service.add_favorite(
        db, str(current_user["id"]), data.id
    )


@discipline_router.delete("/favorite/remove", response_model=DisciplineResponse)
async def remove_from_favorites(
    data: AddFavorite,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await discipline_service.remove_favorite(db, str(current_user["id"]), data.id)


@discipline_router.get("/favorite/my", response_model=List[DisciplineResponse])
async def get_my_favorites(
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await discipline_service.get_user_favorites(db, str(current_user["id"]))
