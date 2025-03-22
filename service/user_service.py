from uuid import uuid4
import re
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from models import User, Session, Role, RoleEnum, UserRole


# TODO: После изменений проверить смену пароля, авторизацию, проверку авторизации и изменение данных юзера.
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

    result = await db.execute(select(Role).where(Role.name == RoleEnum.user))
    user_role_record = result.scalars().first()
    if not user_role_record:
        raise HTTPException(status_code=500, detail="Default user role not found")

    new_user_role = UserRole(user_id=new_user.id, role_id=user_role_record.id)
    db.add(new_user_role)
    await db.commit()

    await db.refresh(new_user)

    return new_user.get_dto()


async def authorization(email: str, password: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="Wrong login")

    if not user.check_password(password):
        raise HTTPException(status_code=400, detail="Wrong password")

    result = await db.execute(select(Session).where(Session.user_id == user.id))
    user_sessions = result.scalars().all()

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

    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=403, detail="Forbidden")

    return user.get_dto()


async def get_current_user(request: Request, db: AsyncSession):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(Session).where(Session.session == token))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=403, detail="Forbidden")

    return user.get_dto()


async def change_user(
        user_id: str,
        first_name: str | None = None,
        surname: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        db: AsyncSession = None
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if email and email != user.email:
        result = await db.execute(
            select(User).where(and_(User.email == email, User.id != user_id))
        )
        if result.scalars().first():
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


async def change_password(user_id: str, password: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    validate_password(password)
    user.set_password(password)
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
