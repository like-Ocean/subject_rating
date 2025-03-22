from fastapi import APIRouter, Depends, Request, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from database import get_db
from service import user_service
from .user_scheme import RegisterModel, Authorization, ChangePasswordModel, ChangeModel

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


@user_router.get("/authorization/check")
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


@user_router.patch("/user/edit")
async def edit_user(user: ChangeModel, db: AsyncSession = Depends(get_db)):
    user_data = await user_service.change_user(
        user.user_id, user.first_name,
        user.surname, user.patronymic, user.email, db
    )
    return user_data


@user_router.patch("/user/edit/password")
async def edit_password(user: ChangePasswordModel, db: AsyncSession = Depends(get_db)):
    await user_service.change_password(user.user_id, user.password, db)
    return Response(status_code=200)


@user_router.get("/")
async def get_all_user(db: AsyncSession = Depends(get_db)):
    user_data = await user_service.get_users(db)
    return user_data


@user_router.get("/user/{user_id}")
async def get_user(user_id, db: AsyncSession = Depends(get_db)):
    user_data = await user_service.get_user(user_id, db)
    return user_data
