from typing import Optional
from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy import or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from models import (
    User, Role, RoleEnum, UserRole, Module, Discipline
)


async def appoint_admin(target_user_id: str, current_user: User, db: AsyncSession):
    if current_user["role"] != RoleEnum.super_admin.value:
        raise HTTPException(status_code=403, detail="Only super-admin can appoint admin")

    target = await db.execute(
        select(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .where(User.id == target_user_id)
    )
    target_user = target.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    role = await db.execute(
        select(Role).where(Role.name == RoleEnum.admin)
    )
    admin_role = role.scalars().first()
    if not admin_role:
        raise HTTPException(status_code=500, detail="Admin role not found in the system")

    if any(ur.role.name == RoleEnum.admin for ur in target_user.user_roles):
        raise HTTPException(400, "User already has admin role")

    if target_user.user_roles:
        target_user.user_roles[0].role_id = admin_role.id
    else:
        db.add(UserRole(user_id=target_user.id, role_id=admin_role.id))

    await db.commit()
    await db.refresh(target_user)
    return target_user.get_dto()


async def remove_admin(target_user_id: str, current_user: User, db: AsyncSession):
    if current_user["role"] != RoleEnum.super_admin.value:
        raise HTTPException(status_code=403, detail="Only super-admin can remove admin role")

    user = await db.execute(
        select(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .where(User.id == target_user_id)
    )
    target_user = user.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    role_result = await db.execute(
        select(Role).where(Role.name == RoleEnum.user)
    )
    user_role = role_result.scalars().first()
    if not user_role:
        raise HTTPException(status_code=500, detail="Default user role not found in the system")

    admin_roles = [ur for ur in target_user.user_roles if ur.role.name == RoleEnum.admin]
    if not admin_roles:
        raise HTTPException(400, "User is not an admin")

    for role in admin_roles:
        role.role_id = user_role.id

    await db.commit()
    await db.refresh(target_user)
    return target_user.get_dto()


async def get_admins(
        db: AsyncSession, page: int = 1,
        size: int = 20, search: Optional[str] = None,
        sort_field: str = "surname", sort_order: str = "asc"
):
    data = (
        select(User).options(selectinload(
            User.user_roles).joinedload(UserRole.role)
        ).join(UserRole).join(Role).where(
            or_(
                Role.name == RoleEnum.admin,
                Role.name == RoleEnum.super_admin
            )
        ).distinct()
    )
    if search:
        data = User.apply_search_filter(data, search)

    total_query = data.with_only_columns(func.count(User.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar_one()

    data = User.apply_sorting(data, sort_field, sort_order)

    total_pages = (total + size - 1) // size
    paginated_query = data.limit(size).offset((page - 1) * size)

    result = await db.execute(paginated_query)
    users = result.unique().scalars().all()

    return {
        "data": [user.get_dto() for user in users],
        "pagination": {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "size": size
        }
    }


async def add_module(module_name: str, current_user: User, db: AsyncSession):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(status_code=403, detail="Only super-admin or admin can add module")

    is_exist = await db.execute(
        select(Module).where(Module.name == module_name)
    )
    module = is_exist.scalars().first()
    if module:
        return module.get_dto()

    new_module = Module(name=module_name)
    db.add(new_module)
    await db.commit()
    await db.refresh(new_module)

    return new_module.get_dto()


async def update_module(module_id: str, new_name: str, current_user: User, db: AsyncSession):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(status_code=403, detail="Only super-admin or admin can update module")

    result = await db.execute(select(Module).where(Module.name == new_name))
    existing_module = result.scalars().first()
    if existing_module and str(existing_module.id) != module_id:
        raise HTTPException(status_code=400, detail="Module with this name already exists")

    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    module.name = new_name
    await db.commit()
    await db.refresh(module)

    return module.get_dto()


async def delete_module(module_id: str, current_user: User, db: AsyncSession):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(status_code=403, detail="Only super-admin or admin can delete module")

    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    result = await db.execute(select(Discipline).where(Discipline.module_id == module_id))
    discipline = result.scalars().first()
    if discipline:
        raise HTTPException(
            status_code=400,
            detail="Module cannot be deleted because there are associated disciplines"
        )

    await db.delete(module)
    await db.commit()

    return Response(status_code=200)


async def get_modules(db: AsyncSession):
    result = await db.execute(select(Module))
    modules = result.unique().scalars().all()
    return [module.get_dto() for module in modules]
