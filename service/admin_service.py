from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models import (
    User, Role, RoleEnum, UserRole, Module, Discipline
)


async def appoint_admin(target_user_id: str, current_user: dict, db: AsyncSession):
    if "SUPER-ADMIN" not in current_user.get("roles", []):
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

    if target_user.user_roles:
        existing_assignment = target_user.user_roles[0]
        if existing_assignment.role.name == RoleEnum.admin:
            raise HTTPException(status_code=400, detail="User is already an admin")
        existing_assignment.role_id = admin_role.id
        await db.commit()
    else:
        new_assignment = UserRole(user_id=target_user_id, role_id=admin_role.id)
        db.add(new_assignment)
        await db.commit()

    await db.refresh(target_user)
    return target_user.get_dto()


async def remove_admin(target_user_id: str, current_user: dict, db: AsyncSession):
    if "SUPER-ADMIN" not in current_user.get("roles", []):
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
    default_role = role_result.scalars().first()
    if not default_role:
        raise HTTPException(status_code=500, detail="Default user role not found in the system")

    updated = False
    for user_role in target_user.user_roles:
        if user_role.role.name == RoleEnum.admin:
            user_role.role_id = default_role.id
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=400, detail="User is not an admin")

    await db.commit()
    await db.refresh(target_user)
    return target_user.get_dto()


async def add_module(module_name: str, current_user: dict, db: AsyncSession):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can add module")

    is_exist = await db.execute(
        select(Module).where(Module.name == module_name)
    )
    module = is_exist.scalars().first()
    if module:
        raise HTTPException(status_code=500, detail="Module is already exist")

    new_module = Module(name=module_name)
    db.add(new_module)
    await db.commit()
    await db.refresh(new_module)

    return new_module.get_dto()


async def update_module(module_id: str, new_name: str, current_user: dict, db: AsyncSession):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
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


async def delete_module(module_id: str, current_user: dict, db: AsyncSession):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
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
