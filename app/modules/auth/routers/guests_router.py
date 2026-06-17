from fastapi import APIRouter, Depends, status
from app.modules.auth.services.guests_services import GuestService
from app.modules.auth.dependencies import get_guest_service
from app.modules.auth.schemas.guests_schema import GuestCreate, GuestResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.modules.auth.schemas.token_schema import Token
from app.modules.auth.auth_middlewares import CurrentGuest

router = APIRouter(prefix="/auth/guests", tags=["guests"])


@router.post(
    "/register", response_model=GuestResponse, status_code=status.HTTP_201_CREATED
)
async def register_guest(
    guest: GuestCreate,
    guest_service: Annotated[GuestService, Depends(get_guest_service)],
):
    return await guest_service.register_guest(guest.model_dump())


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_guest(
    guest: Annotated[OAuth2PasswordRequestForm, Depends()],
    guest_service: Annotated[GuestService, Depends(get_guest_service)],
):
    guest_dict = {"email": guest.username, "password": guest.password}
    return await guest_service.login_guest(guest_dict)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_token: str,
    guest_service: Annotated[GuestService, Depends(get_guest_service)],
):
    return await guest_service.refresh_token(refresh_token)


@router.get("/me", response_model=GuestResponse, status_code=status.HTTP_200_OK)
async def get_current_user(
    guest: CurrentGuest,
):
    return guest
