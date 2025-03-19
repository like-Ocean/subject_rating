from uuid import uuid4
import re
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User, Session


def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'\d', password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")


async def registration(email: str, first_name: str, surname: str, patronymic: str, password: str, db: AsyncSession):
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
