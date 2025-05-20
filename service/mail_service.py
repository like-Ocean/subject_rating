import os
import uuid
from datetime import datetime, timedelta
from fastapi_mail import ConnectionConfig
from fastapi_mail import FastMail, MessageSchema
from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv
from models import PasswordResetToken, User, UserRole
from service.user_service import validate_password


load_dotenv()

RESET_TOKEN_EXPIRE_MINUTES = 30

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
    USE_CREDENTIALS=os.getenv("USE_CREDENTIALS", "True").lower() == "true",
)


async def send_password_reset_email(email: str, token: str):
    fm = FastMail(conf)
    reset_link = f"http://localhost:8000/reset-password?token={token}"

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click the link to reset your password: {reset_link}",
        subtype="html"
    )

    await fm.send_message(message)


async def forgot_password(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    await db.commit()

    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

    db.add(PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    ))
    await db.commit()

    await send_password_reset_email(email, reset_token)


async def reset_password(db: AsyncSession, token: str, new_password: str):
    result = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token == token)
    )
    reset_token = result.scalars().first()

    if not reset_token or reset_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).joinedload(UserRole.role))
        .where(User.id == reset_token.user_id)
    )
    user = result.unique().scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    validate_password(new_password)
    user.set_password(new_password)

    await db.delete(reset_token)
    await db.commit()

    return user.get_dto()
