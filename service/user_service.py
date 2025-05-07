from uuid import uuid4
import re
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from fastapi import HTTPException, Request, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models import User, Session, Role, RoleEnum, UserRole
from sqlalchemy.orm import selectinload, joinedload


def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'\d', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")


async def registration(
        email: str,
        first_name: str,
        surname: str,
        patronymic: str,
        password: str,
        db: AsyncSession
):
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    validate_password(password)

    new_user = User(
        first_name=first_name,
        surname=surname,
        patronymic=patronymic,
        email=email
    )
    new_user.set_password(password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    res = await db.execute(select(Role).where(Role.name == RoleEnum.user))
    user_role_record = res.scalars().first()
    if not user_role_record:
        raise HTTPException(status_code=500, detail="Default user role not found")

    new_user_role = UserRole(user_id=new_user.id, role_id=user_role_record.id)
    db.add(new_user_role)
    await db.commit()

    await db.refresh(new_user)

    return new_user.get_dto()


async def authorization(email: str, password: str, db: AsyncSession):
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
        .where(User.email == email)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="Wrong login")

    if not user.check_password(password):
        raise HTTPException(status_code=400, detail="Wrong password")

    res = await db.execute(select(Session).where(Session.user_id == user.id))
    user_sessions = res.scalars().all()

    if len(user_sessions) >= 5:
        oldest_session = sorted(user_sessions, key=lambda s: str(s.id))[0]
        await db.delete(oldest_session)
        await db.commit()

    new_session = Session(session=str(uuid4()), user_id=user.id)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return user.get_dto(), new_session.session


async def authorization_check(session_token: str, db: AsyncSession):
    result = await db.execute(select(Session).where(Session.session == session_token))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    res = await db.execute(
        select(User)
        .options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
        .where(User.id == session.user_id)
    )
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=403, detail="Forbidden")

    return user.get_dto()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(Session).where(Session.session == token))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    res = await db.execute(
        select(User)
        .options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
        .where(User.id == session.user_id)
    )
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=403, detail="Forbidden")

    return user.get_dto()


async def get_current_user_optional(
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get("session")
    if not token:
        return None

    try:
        result = await db.execute(select(Session).where(Session.session == token))
        session = result.scalars().first()
        if not session:
            return None

        res = await db.execute(
            select(User)
            .options(
                joinedload(User.user_roles).joinedload(UserRole.role)
            )
            .where(User.id == session.user_id)
        )
        user = res.scalars().first()
        return user.get_dto() if user else None
    except Exception as e:
        return None


async def change_user(
        user_id: str,
        first_name: str | None = None,
        surname: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        db: AsyncSession = None
):
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
        .where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if email and email != user.email:
        res = await db.execute(
            select(User).where(and_(User.email == email, User.id != user_id))
        )
        if res.scalars().first():
            raise HTTPException(status_code=400, detail="User with this email already exists")

    if first_name is not None:
        user.first_name = first_name
    if surname is not None:
        user.surname = surname
    if patronymic is not None:
        user.patronymic = patronymic
    if email is not None:
        user.email = email

    await db.commit()
    await db.refresh(user)

    return user.get_dto()


async def change_password(
        user_id: str, old_password: str,
        new_password: str, db: AsyncSession
):
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
        .where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not user.check_password(old_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    validate_password(new_password)
    user.set_password(new_password)

    await db.commit()
    await db.refresh(user)
    return user.get_dto()


async def get_users(db: AsyncSession):
    result = await db.execute(
        select(User).options(
            selectinload(User.user_roles).joinedload(UserRole.role)
        )
    )
    users = result.unique().scalars().all()
    return [user.get_dto() for user in users]


async def get_user(user_id: str, db: AsyncSession):
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
        .where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return user.get_dto()


async def delete_user(
        db: AsyncSession,
        user_id: str,
        current_user: User
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(status_code=403, detail="Only super-admin or admin can delete user")

    result = await db.execute(
        select(User)
        .options(
            selectinload(User.user_roles).joinedload(UserRole.role),
            selectinload(User.reviews),
            selectinload(User.favorites),
            selectinload(User.votes),
            selectinload(User.sessions)
        )
        .where(User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(404, "User not found")

    if user_id == current_user["id"]:
        raise HTTPException(400, "Self-deletion is not allowed")

    user_role = user.user_roles[0].role.name if user.user_roles else RoleEnum.user

    if user_role in {RoleEnum.admin, RoleEnum.super_admin}:
        if current_user["role"] != RoleEnum.super_admin.value:
            raise HTTPException(403, "Only SUPER_ADMIN can delete admins")

    try:
        await db.delete(user)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")

    return Response(status_code=200)
