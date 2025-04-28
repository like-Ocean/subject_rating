from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from models import User
from database import get_db
from service import user_service
from .user_scheme import RegisterModel, Authorization, ChangePasswordModel, ChangeModel
from response_models import UserResponse

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/registration", response_model=UserResponse)
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


@user_router.post("/authorization", response_model=UserResponse)
async def authorization(user: Authorization, db: AsyncSession = Depends(get_db)):
    user_data, session = await user_service.authorization(user.email, user.password, db)
    response = JSONResponse(content=user_data)
    response.set_cookie('session', session, httponly=True)
    return response


@user_router.get("/authorization/check", response_model=UserResponse)
async def authorization_check(request: Request, db: AsyncSession = Depends(get_db)):
    session = request.cookies.get('session')
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = await user_service.authorization_check(session, db)

    return user


@user_router.post("/user/logout")
async def logout():
    response = Response(status_code=200)
    response.set_cookie(key="session", value="", httponly=True)
    return response


@user_router.patch("/user/edit", response_model=UserResponse)
async def edit_user(
        user: ChangeModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)

):
    user_data = await user_service.change_user(
        user.id, user.first_name,
        user.surname, user.patronymic, user.email, db
    )
    return user_data


@user_router.patch("/user/edit/password", response_model=UserResponse)
async def edit_password(
        user: ChangePasswordModel,
        current_user: User = Depends(user_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await user_service.change_password(
        user.id,
        user.old_password,
        user.new_password,
        db
    )


@user_router.get("/", response_model=List[UserResponse])
async def get_all_user(db: AsyncSession = Depends(get_db)):
    user_data = await user_service.get_users(db)
    return user_data


@user_router.get("/user/{id}", response_model=UserResponse)
async def get_user(id, db: AsyncSession = Depends(get_db)):
    user_data = await user_service.get_user(id, db)
    return user_data


@user_router.delete("/admin/user/{id}/delete")
async def delete_user(
    id: str,
    current_user: dict = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.delete_user(db, id, current_user)
