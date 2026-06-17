from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models.users_model import User
from app.utils.exceptions import RepositoryException
from app.utils.logging import LoggerFactory
import uuid
logger = LoggerFactory.get_logger(__name__)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user: dict) -> User:
        logger.info("[UserRepository] Creating user")
        try:
            new_user = User(**user)
            self.session.add(new_user)
            await self.session.commit()
            await self.session.refresh(new_user)
            logger.info("[UserRepository] User created successfully")
            return new_user
        except Exception as e:
            logger.error(f"[UserRepository] Error creating user: {str(e)}")
            await self.session.rollback()
            raise RepositoryException(str(e))

    async def get_user_by_email(self, email: str) -> User | None:
        logger.info("[UserRepository] Getting user by email")
        try:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            logger.error(f"[UserRepository] Error getting user by email: {str(e)}")
            raise RepositoryException(str(e))

    async def get_user_by_id(self, user_id: str) -> User | None:
        logger.info("[UserRepository] Getting user by ID")
        try:
            result = await self.session.execute(
                select(User).where(User.id == uuid.UUID(user_id))
            )
            user = result.scalar_one_or_none()
            return user
        except Exception as e:
            logger.error(f"[UserRepository] Error getting user by ID: {str(e)}")
            raise RepositoryException(str(e))