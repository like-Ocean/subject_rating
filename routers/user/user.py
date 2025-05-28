from typing import Optional
from fastapi import (
    APIRouter, Depends, Request,
    HTTPException, Response, Query
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from models import User
from database import get_db
from service import user_service, mail_service
from .user_scheme import (
    RegisterModel, Authorization, ChangePasswordModel, ChangeModel,
    ForgotPasswordRequest, ResetPasswordRequest
)
from response_models import UserResponse, PaginatedResponse

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


@user_router.get("/", response_model=PaginatedResponse[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(
        20, ge=1, le=100,
        description="Поиск по имени или фамилии или отчеству"
    ),
    search: Optional[str] = Query(None),
    sort_field: str = Query(
        "surname",
        description="Поле для сортировки (surname, first_name)"
    ),
    sort_order: str = Query(
        "asc",
        description="Порядок сортировки (asc/desc)"
    ),
    current_user: User = Depends(user_service.get_current_user)
):
    return await user_service.get_users(
        db, current_user, page, size, search,
        sort_field, sort_order
    )


@user_router.get("/user/{id}", response_model=UserResponse)
async def get_user(id, db: AsyncSession = Depends(get_db)):
    user_data = await user_service.get_user(id, db)
    return user_data


@user_router.delete("/admin/user/{id}/delete")
async def delete_user(
    id: str,
    current_user: User = Depends(user_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.delete_user(db, id, current_user)


@user_router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    await mail_service.forgot_password(db, data.email)
    return {"detail": "If the email exists, a reset link will be sent"}


@user_router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    return await mail_service.reset_password(db, data.token, data.new_password)
