from app.repository.users_repo import UserRepository
from app.utils.exceptions import (
    ServiceException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.utils.logging import LoggerFactory
from app.models.users_model import UserModel
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

logger = LoggerFactory.get_logger(__name__)


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, user: dict) -> UserModel:
        logger.info("[UserService] Creating user")
        existing_email = await self.user_repository.get_user_by_email(user["email"])
        if existing_email:
            raise UserAlreadyExistsException(
                f"User with email {user['email']} already exists"
            )
        user["hashed_password"] = get_password_hash(user["password"])
        user.pop("password")
        try:
            new_user = await self.user_repository.register_user(user)
            logger.info("[UserService] User created successfully")
            return new_user

        except UserAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"[UserService] Error creating user: {str(e)}")
            raise ServiceException(str(e))

    async def get_user_by_email(self, email: str) -> UserModel:
        logger.info("[UserService] Getting user by email")
        try:
            user = await self.user_repository.get_user_by_email(email)
            if not user:
                raise UserNotFoundException(
                    "User not found", f"User with email {email} not found"
                )
            logger.info("[UserService] User found successfully")
            return user
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[UserService] Error getting user by email: {str(e)}")
            raise ServiceException(str(e))

    async def get_user_by_id(self, user_id: str) -> UserModel:
        logger.info("[UserService] Getting user by ID")
        try:
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundException(
                    "User not found", f"User with ID {user_id} not found"
                )
            logger.info("[UserService] User found successfully")
            return user
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[UserService] Error getting user by ID: {str(e)}")
            raise ServiceException(str(e))

    async def login_user(self, user: dict) -> dict:
        logger.info("[UserService] Logging in user")
        try:
            existing_user = await self.user_repository.get_user_by_email(user["email"])
            if not existing_user:
                raise UserNotFoundException(
                    "Invalid credentials", f"User with email {user['email']} not found"
                )
            if not verify_password(
                user["hashed_password"], existing_user.hashed_password
            ):
                raise UserNotFoundException(
                    "Invalid credentials", f"Invalid password for user {user['email']}"
                )
            token = create_access_token({"sub": str(existing_user.id)})
            refresh_token = create_refresh_token({"sub": str(existing_user.id)})
            logger.info("[UserService] User logged in successfully")
            return {
                "access_token": token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[UserService] Error logging in user: {str(e)}")
            raise ServiceException(str(e))

    async def refresh_token(self, refresh_token: str) -> dict:
        logger.info("[UserService] Refreshing token")
        try:
            user_id = verify_refresh_token(refresh_token)
            if not user_id:
                raise UserNotFoundException(
                    "Invalid credentials", "Invalid refresh token"
                )
            token = create_access_token({"sub": str(user_id)})
            refresh_token = create_refresh_token({"sub": str(user_id)})
            logger.info("[UserService] Token refreshed successfully")
            return {
                "access_token": token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[UserService] Error refreshing token: {str(e)}")
            raise ServiceException(str(e))
