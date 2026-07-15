"""用户与认证接口。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import CurrentUserDep, DbSession

from .schemas import TokenOut, UserOut, UserRegister, UserUpdate
from .service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: DbSession) -> UserOut:
    user = await UserService(db).register(data)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenOut)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> TokenOut:
    user, token = await UserService(db).authenticate(form.username, form.password)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def read_me(current: CurrentUserDep, db: DbSession) -> UserOut:
    user = await UserService(db).get(current.id)
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(data: UserUpdate, current: CurrentUserDep, db: DbSession) -> UserOut:
    user = await UserService(db).update_profile(current.id, data)
    return UserOut.model_validate(user)
