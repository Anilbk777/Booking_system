from app.modules.auth.repositories.guests_repo import GuestRepository
from app.modules.auth.models.guests_model import Guest
from app.modules.auth.services.auth_services import AuthService
from app.utils.exceptions import (
    ServiceException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class GuestService:
    def __init__(self, guest_repository: GuestRepository, auth_service: AuthService):
        self.guest_repository = guest_repository
        self.auth_service = auth_service

    async def register_guest(self, guest: dict) -> Guest:
        logger.info("[GuestService] Creating guest")
        existing_email = await self.guest_repository.get_guest_by_email(guest["email"])
        if existing_email:
            raise UserAlreadyExistsException(
                f"Guest with email {guest['email']} already exists"
            )
        guest["password_hash"] = self.auth_service.get_password_hash(guest["password"])
        guest.pop("password")
        try:
            new_guest = await self.guest_repository.register_guest(guest)
            logger.info("[GuestService] Guest created successfully")
            return new_guest
        except UserAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"[GuestService] Error creating guest: {str(e)}")
            raise ServiceException(str(e))

    async def get_guest_by_email(self, email: str) -> Guest:
        logger.info("[GuestService] Getting guest by email")
        try:
            guest = await self.guest_repository.get_guest_by_email(email)
            if not guest:
                raise UserNotFoundException(
                    "Guest not found", f"Guest with email {email} not found"
                )
            logger.info("[GuestService] Guest found successfully")
            return guest
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[GuestService] Error getting guest by email: {str(e)}")
            raise ServiceException(str(e))

    async def get_guest_by_id(self, guest_id: str) -> Guest:
        logger.info("[GuestService] Getting guest by ID")
        try:
            guest = await self.guest_repository.get_guest_by_id(guest_id)
            if not guest:
                raise UserNotFoundException(
                    "Guest not found", f"Guest with ID {guest_id} not found"
                )
            logger.info("[GuestService] Guest found successfully")
            return guest
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[GuestService] Error getting guest by ID: {str(e)}")
            raise ServiceException(str(e))

    async def login_guest(self, guest: dict) -> dict:
        logger.info("[GuestService] Logging in guest")
        try:
            existing_guest = await self.guest_repository.get_guest_by_email(
                guest["email"]
            )
            if not existing_guest:
                raise UserNotFoundException(
                    "Invalid credentials",
                    f"Guest with email {guest['email']} not found",
                )
            if not self.auth_service.verify_password(
                guest["password"], existing_guest.password_hash
            ):
                raise UserNotFoundException(
                    "Invalid credentials",
                    f"Invalid password for guest {guest['email']}",
                )
            token = self.auth_service.create_access_token(
                {"sub": str(existing_guest.id), "role": "guest"}
            )
            refresh_token = self.auth_service.create_refresh_token(
                {"sub": str(existing_guest.id), "role": "guest"}
            )
            logger.info("[GuestService] Guest logged in successfully")
            return {
                "access_token": token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[GuestService] Error logging in guest: {str(e)}")
            raise ServiceException(str(e))

    async def refresh_token(self, refresh_token: str) -> dict:
        logger.info("[GuestService] Refreshing token")
        try:
            user_id = self.auth_service.verify_refresh_token(refresh_token)
            if not user_id:
                raise UserNotFoundException(
                    "Invalid credentials", "Invalid refresh token"
                )
            token = self.auth_service.create_access_token({"sub": str(user_id), "role": "guest"})
            refresh_token = self.auth_service.create_refresh_token(
                {"sub": str(user_id), "role": "guest"}
            )
            logger.info("[GuestService] Token refreshed successfully")
            return {
                "access_token": token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[GuestService] Error refreshing token: {str(e)}")
            raise ServiceException(str(e))
