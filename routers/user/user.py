from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from database import get_db
from service import user_service
from .user_scheme import RegisterModel, Authorization

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/registration")
async def registration(user: RegisterModel, db: AsyncSession = Depends(get_db)):
    user_data = await user_service.registration(
        user.email,
        user.first_name,
        user.surname,
        user.patronymic,
        user.password,
        db
    )
    return user_data


@user_router.post("/authorization")
async def authorization(user: Authorization, db: AsyncSession = Depends(get_db)):
    user_data, session = await user_service.authorization(user.email, user.password, db)
    response = JSONResponse(content=user_data)
    response.set_cookie('session', session, httponly=True)
    return response
