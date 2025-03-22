from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Role, UserRole, RoleEnum


async def init_roles(db: AsyncSession):
    existing_roles = await db.execute(select(Role))
    existing_roles = {role.name for role in existing_roles.scalars().all()}

    roles_to_create = [
        Role(name=role) for role in RoleEnum if role not in existing_roles
    ]

    if roles_to_create:
        db.add_all(roles_to_create)
        await db.commit()


async def init_super_admin(db: AsyncSession):
    result = await db.execute(
        select(User).join(User.user_roles).join(Role).where(Role.name == RoleEnum.super_admin)
    )
    super_admin = result.scalars().first()

    if not super_admin:
        default_email = "admin@example.com"
        default_password = "Admin123_"

        result = await db.execute(select(User).where(User.email == default_email))
        super_admin = result.scalars().first()
        if not super_admin:
            super_admin = User(
                first_name="Super",
                surname="Admin",
                patronymic=None,
                email=default_email,
            )
            super_admin.set_password(default_password)
            db.add(super_admin)
            await db.commit()
            await db.refresh(super_admin)

        result = await db.execute(select(Role).where(Role.name == RoleEnum.super_admin))
        super_admin_role = result.scalars().first()
        if not super_admin_role:
            super_admin_role = Role(name=RoleEnum.super_admin)
            db.add(super_admin_role)
            await db.commit()
            await db.refresh(super_admin_role)

        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == super_admin.id,
                UserRole.role_id == super_admin_role.id
            )
        )
        user_role = result.scalars().first()
        if not user_role:
            user_role = UserRole(user_id=super_admin.id, role_id=super_admin_role.id)
            db.add(user_role)
            await db.commit()

    return super_admin
