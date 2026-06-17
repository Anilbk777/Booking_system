from fastapi import Depends
from app.modules.auth.repositories.guests_repo import GuestRepository
from app.modules.auth.repositories.users_repo import UserRepository
from app.modules.auth.services.auth_services import AuthService
from app.modules.auth.services.guests_services import GuestService
from app.modules.auth.services.users_services import UserService
from app.config.database_config import get_db


def get_guest_auth_service() -> AuthService:
    return AuthService()


# --- Guest Dependencies ---


def get_guest_repository(db=Depends(get_db)) -> GuestRepository:
    return GuestRepository(db)


def get_guest_service(
    guest_repository: GuestRepository = Depends(get_guest_repository),
    auth_service: AuthService = Depends(get_guest_auth_service),
) -> GuestService:
    return GuestService(guest_repository, auth_service)


# --- User Dependencies ---


def get_user_repository(db=Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_guest_auth_service),
) -> UserService:
    return UserService(user_repository, auth_service)
