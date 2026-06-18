from app.modules.pms.repositories.room_repo import RoomRepository
from app.modules.pms.models.rooms_model import RoomType
from app.modules.pms.repositories.properties_repo import PropertyRepository

from app.utils.exceptions import (
    ServiceException,
    PropertyNotFoundException,
    UnauthorizedException,
)
from app.utils.logging import LoggerFactory
import uuid

logger = LoggerFactory.get_logger(__name__)


class RoomService:
    def __init__(self, room_repo: RoomRepository, property_repo: PropertyRepository):
        self.room_repo = room_repo
        self.property_repo = property_repo

    async def _validate_property(self, property_id: uuid.UUID, tenant_id: uuid.UUID):
        property_obj = await self.property_repo.get_property_by_id(
            property_id, tenant_id
        )
        if not property_obj:
            raise PropertyNotFoundException("Property not found")

        if property_obj.tenant_id != tenant_id:
            raise UnauthorizedException("You do not own this property")
        return property_obj

    async def create_room_type(
        self, room_type_data: dict, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> RoomType:
        logger.info(
            f"[RoomService] Creating room type: {room_type_data} for property {property_id}"
        )

        try:
            await self._validate_property(property_id, tenant_id)
            room_type_data["property_id"] = property_id
            return await self.room_repo.create_room_type(room_type_data)

        except (PropertyNotFoundException, UnauthorizedException) as e:
            logger.warning(f"[RoomService] Error creating room type: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[RoomService] Error creating room type: {str(e)}")
            raise ServiceException(str(e))

    async def get_room_types(
        self, tenant_id: uuid.UUID, property_id: uuid.UUID
    ) -> list[RoomType]:
        logger.info(
            f"[RoomService] Getting room types for property {property_id}"
        )
        try:
            await self._validate_property(property_id, tenant_id)
            room_types = await self.room_repo.get_room_types(property_id)
            return room_types
        except (PropertyNotFoundException, UnauthorizedException) as e:
            logger.warning(f"[RoomService] Error getting room types: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[RoomService] Error getting room types: {str(e)}")
            raise ServiceException(str(e))
  