from app.modules.pms.models.rooms_model import RoomType, PropertyRoomUnit, RatePlan
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.utils.exceptions import RepositoryException
from app.utils.logging import LoggerFactory
import uuid

logger = LoggerFactory.get_logger(__name__)


class RoomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_room_type(self, room_type: dict) -> RoomType:
        logger.info(f"[RoomRepository] Creating room type: {room_type}")
        try:
            new_room_type = RoomType(**room_type)
            self.db.add(new_room_type)
            await self.db.commit()
            await self.db.refresh(new_room_type)
            logger.info("[RoomRepository] Room type created successfully")
            return new_room_type
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[RoomRepository] Error creating room type: {str(e)}")
            raise RepositoryException(str(e))

    async def get_room_types(self, property_id: uuid.UUID) -> list[RoomType]:
        logger.info(f"[RoomRepository] Getting room types for property {property_id}")
        try:
            result = await self.db.execute(
                select(RoomType).where(RoomType.property_id == property_id)
            )
            room_types = result.scalars().all()
            logger.info("[RoomRepository] Room types fetched successfully")
            return room_types
        except Exception as e:
            logger.error(f"[RoomRepository] Error fetching room types: {str(e)}")
            raise RepositoryException(str(e))
