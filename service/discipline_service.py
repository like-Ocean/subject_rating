from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from models import DisciplineFormatEnum, Module, Discipline


async def create_discipline(
        db: AsyncSession,
        current_user: dict,
        name: str,
        format_value: str,
        module_id: str,
        description: Optional[str] = None,
        modeus_link: Optional[str] = None,
        presentation_link: Optional[str] = None,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can create discipline")

    try:
        discipline_format = DisciplineFormatEnum(format_value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат дисциплины. Ожидалось одно из: 'онлайн', 'традиционный' или 'смешанный'"
        )

    try:
        result = await db.execute(select(Module).where(Module.id == module_id))
    except DBAPIError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid module_id. Please provide a valid UUID."
        ) from e

    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    result = await db.execute(
        select(Discipline).where(
            Discipline.name == name,
            Discipline.module_id == module_id
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Discipline already exists in this module")

    new_discipline = Discipline(
        name=name,
        format=discipline_format,
        description=description,
        modeus_link=modeus_link,
        presentation_link=presentation_link,
        module_id=module_id
    )
    db.add(new_discipline)
    await db.commit()
    await db.refresh(new_discipline)
    return new_discipline.get_dto()


async def update_discipline(
    db: AsyncSession,
    current_user: dict,
    discipline_id: str,
    name: Optional[str] = None,
    format_value: Optional[str] = None,
    module_id: Optional[str] = None,
    description: Optional[str] = None,
    modeus_link: Optional[str] = None,
    presentation_link: Optional[str] = None,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can update discipline"
        )

    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = result.scalars().first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    if module_id:
        try:
            result = await db.execute(select(Module).where(Module.id == module_id))
        except DBAPIError as e:
            raise HTTPException(
                status_code=400, detail="Invalid module_id. Please provide a valid UUID."
            ) from e
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        discipline.module_id = module_id

    if format_value:
        try:
            discipline_format = DisciplineFormatEnum(format_value)
        except ValueError:
            raise HTTPException
        discipline.format = discipline_format

    if name:
        check_module_id = module_id if module_id else discipline.module_id
        result = await db.execute(
            select(Discipline).where(
                and_(
                    Discipline.name == name,
                    Discipline.module_id == check_module_id,
                    Discipline.id != discipline_id
                )
            )
        )
        existing = result.scalars().first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Discipline with this name already exists in this module"
            )
        discipline.name = name

    if description is not None:
        discipline.description = description
    if modeus_link is not None:
        discipline.modeus_link = modeus_link
    if presentation_link is not None:
        discipline.presentation_link = presentation_link

    await db.commit()
    await db.refresh(discipline)
    return discipline.get_dto()


async def delete_discipline(
    db: AsyncSession,
    current_user: dict,
    discipline_id: str
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can delete discipline"
        )

    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = result.scalars().first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    await db.delete(discipline)
    await db.commit()

    return {"detail": "Discipline deleted successfully"}


# TODO: Сделать чтобы приходили с dto:
#  рейтинг (среднее из всех отзывов)
#  количество отзывов количество добавлений в избранное
async def get_disciplines(db: AsyncSession):
    discipline = await db.execute(select(Discipline))
    disciplines = discipline.unique().scalars().all()
    return [discipline.get_dto() for discipline in disciplines]


async def get_discipline(db: AsyncSession, discipline_id: str):
    res = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = res.scalars().first()
    if not discipline:
        raise HTTPException(status_code=400, detail="Discipline not found")

    return discipline.get_dto()


# TODO: не тестил( ну и не написал ещё :) )
async def search_disciplines(
    db: AsyncSession,
    module_search: Optional[str] = None,  # Фильтр по наименованию модуля (подстрока)
    format_filter: Optional[str] = None,
    sort_by: Optional[str] = "rating",    # "rating", "reviews", "latest"
    sort_order: Optional[str] = "desc"      # "asc" или "desc"
):
    pass
