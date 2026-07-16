"""用户与认证接口。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import CurrentUser, CurrentUserDep, DbSession
from app.models.enums import UserRole

from .schemas import TokenOut, UserOut, UserRegister, UserUpdate
from .service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def _role_of(current: CurrentUser) -> UserRole:
    # JWT 里的 role 是自由字符串，非法值安全回退到最低权限 user。
    try:
        return UserRole(current.role)
    except ValueError:
        return UserRole.user


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
    user = await UserService(db).get(current.id, role=_role_of(current))
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(data: UserUpdate, current: CurrentUserDep, db: DbSession) -> UserOut:
    user = await UserService(db).update_profile(current.id, data, role=_role_of(current))
    return UserOut.model_validate(user)
