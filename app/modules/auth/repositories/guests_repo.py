
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models.guests_model import Guest
from app.utils.exceptions import RepositoryException
from app.utils.logging import LoggerFactory
import uuid
logger = LoggerFactory.get_logger(__name__)

class GuestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_guest(self, guest: dict) -> Guest:
        logger.info("[GuestRepository] Creating guest")
        try:
            new_guest = Guest(**guest)
            self.session.add(new_guest)
            await self.session.commit()
            await self.session.refresh(new_guest)
            logger.info("[GuestRepository] Guest created successfully")
            return new_guest
        except Exception as e:
            logger.error(f"[GuestRepository] Error creating guest: {str(e)}")
            await self.session.rollback()
            raise RepositoryException(str(e))


    async def get_guest_by_email(self, email: str) -> Guest | None:
        logger.info("[GuestRepository] Getting guest by email")
        try:
            result = await self.session.execute(
                select(Guest).where(Guest.email == email)
            )
            guest = result.scalar_one_or_none()
            return guest
        except Exception as e:
            logger.error(f"[GuestRepository] Error getting guest by email: {str(e)}")
            raise RepositoryException(str(e))

    async def get_guest_by_id(self, guest_id: str) -> Guest | None:
        logger.info("[GuestRepository] Getting guest by ID")
        try:
            result = await self.session.execute(
                select(Guest).where(Guest.id == uuid.UUID(guest_id))
            )
            guest = result.scalar_one_or_none()
            return guest
        except Exception as e:
            logger.error(f"[GuestRepository] Error getting guest by ID: {str(e)}")
            raise RepositoryException(str(e))
