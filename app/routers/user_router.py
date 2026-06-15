from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.users_schema import (
    UserRegisterRequest,
    UserResponse,
    Token,
)
from app.services.user_service import UserService
from app.utils.dependencies import get_user_service, CurrentUser

router = APIRouter(prefix="/v1/api", tags=["Users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserRegisterRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return await user_service.register_user(user.model_dump())


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(
    user: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_dict = {"email": user.username, "hashed_password": user.password}
    return await user_service.login_user(user_dict)


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    return current_user
