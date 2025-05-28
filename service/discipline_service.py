from typing import Optional, List
from fastapi import HTTPException, Response
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from models import (
    DisciplineFormatEnum, Module,
    Discipline, User, Favorite, RoleEnum
)


def sort_disciplines(disciplines: List[Discipline], sort_by: str, sort_order: str):
    if sort_by not in ("rating", "reviews", "latest"):
        raise HTTPException(400, detail="Invalid sort_by parameter")

    if sort_order not in ("asc", "desc"):
        raise HTTPException(400, detail="Invalid sort_order parameter")

    reverse = (sort_order == "desc")

    def get_rating(d: Discipline):
        grades = [r.grade for r in d.reviews if r.grade is not None]
        return sum(grades) / len(grades) if grades else 0.0

    def get_reviews_count(d: Discipline):
        return len(d.reviews)

    def get_latest_date(d: Discipline):
        dates = [r.created_at for r in d.reviews]
        if dates:
            return max(dates)
        return datetime.min.replace(tzinfo=timezone.utc)

    sort_key = {
        "rating": get_rating,
        "reviews": get_reviews_count,
        "latest": get_latest_date
    }[sort_by]

    return sorted(disciplines, key=sort_key, reverse=reverse)


async def create_discipline(
        db: AsyncSession,
        current_user: User,
        name: str,
        format_value: str,
        module_id: str,
        description: Optional[str] = None,
        modeus_link: Optional[str] = None,
        presentation_link: Optional[str] = None,
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can create discipline"
        )

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

    await db.refresh(new_discipline, attribute_names=['module'])
    if not new_discipline.module:
        raise HTTPException(500, "Module not loaded after creation")

    res = await db.execute(
        Discipline.get_joined_data()
        .where(Discipline.id == new_discipline.id)
        .options(
            selectinload(Discipline.module),
            selectinload(Discipline.reviews),
            selectinload(Discipline.favorites)
        )
    )
    new_discipline = res.scalars().first()

    return new_discipline.get_dto()


async def update_discipline(
        db: AsyncSession,
        current_user: User,
        discipline_id: str,
        name: Optional[str] = None,
        format_value: Optional[str] = None,
        module_id: Optional[str] = None,
        description: Optional[str] = None,
        modeus_link: Optional[str] = None,
        presentation_link: Optional[str] = None,
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
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
                status_code=400,
                detail="Invalid module_id. Please provide a valid UUID."
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

    # Возможно такой вариант изменеия будет лучше
    # if modeus_link is not None or modeus_link == "":
    #     discipline.modeus_link = modeus_link
    if description is not None:
        discipline.description = description
    if modeus_link is not None:
        discipline.modeus_link = modeus_link
    if presentation_link is not None:
        discipline.presentation_link = presentation_link

    await db.commit()

    result = await db.execute(
        Discipline.get_joined_data()
        .where(Discipline.id == discipline_id)
    )
    discipline = result.scalars().first()

    return discipline.get_dto()


async def delete_discipline(
        db: AsyncSession,
        current_user: User,
        discipline_id: str
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
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

    return Response(status_code=200)


async def get_disciplines(db: AsyncSession):
    result = await db.execute(Discipline.get_joined_data())
    disciplines = result.scalars().all()
    return [discipline.get_dto() for discipline in disciplines]


async def get_discipline(db: AsyncSession, discipline_id: str):
    res = await db.execute(
        Discipline.get_joined_data()
        .where(Discipline.id == discipline_id)
    )
    discipline = res.scalars().first()
    if not discipline:
        raise HTTPException(status_code=400, detail="Discipline not found")

    return discipline.get_dto()


async def search_disciplines(
        db: AsyncSession,
        page: int,
        size: int,
        name_search: Optional[str] = None,
        module_search: Optional[str] = None,
        format_filter: Optional[str] = None,
        sort_by: Optional[str] = "rating",  # "rating", "reviews", "latest"
        sort_order: Optional[str] = "desc",  # "asc" или "desc"
):
    data = Discipline.get_joined_data()
    query = Discipline.apply_filters(
        data,
        name_search=name_search,
        module_search=module_search,
        format_filter=format_filter
    )

    total_query = query.with_only_columns(func.count(Discipline.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar_one()

    total_pages = (total + size - 1) // size
    paginated_query = query.limit(size).offset((page - 1) * size)

    result = await db.execute(paginated_query)
    disciplines = result.unique().scalars().all()

    sorted_disciplines = sort_disciplines(disciplines, sort_by, sort_order)

    return {
        "data": [discipline.get_dto() for discipline in sorted_disciplines],
        "pagination": {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "size": size
        }
    }


async def add_favorite(db: AsyncSession, user_id: str, discipline_id: str):
    user_data = await db.execute(select(User).where(User.id == user_id))
    user = user_data.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    discipline_data = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = discipline_data.scalars().first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    fav_data = await db.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == user_id,
                Favorite.discipline_id == discipline_id
            )
        )
    )
    existing = fav_data.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Discipline already in favorites")

    favorite = Favorite(user_id=user_id, discipline_id=discipline_id)
    db.add(favorite)
    await db.commit()

    query = Discipline.get_joined_data().where(Discipline.id == discipline_id)
    result = await db.execute(query)
    updated_discipline = result.scalars().first()

    return updated_discipline.get_dto()


async def remove_favorite(db: AsyncSession, user_id: str, discipline_id: str):
    user_data = await db.execute(select(User).where(User.id == user_id))
    user = user_data.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    discipline_data = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = discipline_data.scalars().first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    result = await db.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == user_id,
                Favorite.discipline_id == discipline_id
            )
        )
    )
    favorite = result.scalars().first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await db.delete(favorite)
    await db.commit()

    query = Discipline.get_joined_data().where(Discipline.id == discipline_id)
    result = await db.execute(query)
    updated_discipline = result.scalars().first()

    return updated_discipline.get_dto()


async def get_user_favorites(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        size: int = 20,
        name_search: Optional[str] = None,
        module_search: Optional[str] = None,
        format_filter: Optional[str] = None,
        sort_by: Optional[str] = "rating",
        sort_order: Optional[str] = "desc"
):
    data = Discipline.get_favorites(user_id)
    query = Discipline.apply_filters(
        data,
        name_search=name_search,
        module_search=module_search,
        format_filter=format_filter
    )

    total_query = query.with_only_columns(func.count(Discipline.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar_one()
    total_pages = (total + size - 1) // size
    paginated_query = query.limit(size).offset((page - 1) * size)

    result = await db.execute(paginated_query)
    disciplines = result.unique().scalars().all()

    sorted_disciplines = sort_disciplines(disciplines, sort_by, sort_order)

    return {
        "data": [discipline.get_dto() for discipline in sorted_disciplines],
        "pagination": {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "size": size
        }
    }
