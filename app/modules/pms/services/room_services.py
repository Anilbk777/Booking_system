from app.modules.pms.repositories.room_repo import RoomRepository
from app.modules.pms.models.rooms_model import RoomType, RatePlan, DateOverride, DiscountCode
from app.modules.pms.repositories.properties_repo import PropertyRepository

from app.utils.exceptions import (
    ServiceException,
    PropertyNotFoundException,
    UnauthorizedException,
    RoomTypeNotFoundException,
    RatePlanNotFoundException,
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

    async def get_room_type_by_id(
        self, room_type_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> RoomType:
        try:
            await self._validate_property(property_id, tenant_id)
            room_type = await self.room_repo.get_room_type_by_id(room_type_id, property_id)
            if not room_type:
                raise RoomTypeNotFoundException(f"Room type {room_type_id} not found")
            return room_type
        except Exception as e:
            raise ServiceException(str(e))

    async def update_room_type(
        self, room_type_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID, data: dict
    ) -> RoomType:
        try:
            await self._validate_property(property_id, tenant_id)
            updated = await self.room_repo.update_room_type(room_type_id, property_id, data)
            if not updated:
                raise RoomTypeNotFoundException(f"Room type {room_type_id} not found")
            return updated
        except Exception as e:
            raise ServiceException(str(e))

    async def delete_room_type(
        self, room_type_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> bool:
        try:
            await self._validate_property(property_id, tenant_id)
            return await self.room_repo.delete_room_type(room_type_id, property_id)
        except Exception as e:
            raise ServiceException(str(e))

    # --- Rate Plans ---

    async def create_rate_plan(self, data: dict, property_id: uuid.UUID, tenant_id: uuid.UUID) -> RatePlan:
        await self._validate_property(property_id, tenant_id)
        data["property_id"] = property_id
        return await self.room_repo.create_rate_plan(data)

    async def get_rate_plans(self, property_id: uuid.UUID, tenant_id: uuid.UUID, room_type_id: uuid.UUID = None) -> list[RatePlan]:
        await self._validate_property(property_id, tenant_id)
        return await self.room_repo.get_rate_plans(property_id, room_type_id)

    async def update_rate_plan(self, rate_plan_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID, data: dict) -> RatePlan:
        await self._validate_property(property_id, tenant_id)
        # Verify ownership of rate plan
        plan = await self.room_repo.get_rate_plan_by_id(rate_plan_id)
        if not plan or plan.property_id != property_id:
            raise RatePlanNotFoundException(f"Rate plan {rate_plan_id} not found")
        return await self.room_repo.update_rate_plan(rate_plan_id, data)

    async def delete_rate_plan(self, rate_plan_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        await self._validate_property(property_id, tenant_id)
        plan = await self.room_repo.get_rate_plan_by_id(rate_plan_id)
        if not plan or plan.property_id != property_id:
            raise RatePlanNotFoundException(f"Rate plan {rate_plan_id} not found")
        return await self.room_repo.delete_rate_plan(rate_plan_id)

    # --- Date Overrides ---

    async def create_date_override(self, data: dict, property_id: uuid.UUID, tenant_id: uuid.UUID) -> DateOverride:
        await self._validate_property(property_id, tenant_id)
        data["property_id"] = property_id
        return await self.room_repo.create_date_override(data)

    async def get_date_overrides(self, property_id: uuid.UUID, tenant_id: uuid.UUID) -> list[DateOverride]:
        await self._validate_property(property_id, tenant_id)
        return await self.room_repo.get_date_overrides(property_id)

    # --- Discount Codes ---

    async def create_discount_code(self, data: dict, property_id: uuid.UUID, tenant_id: uuid.UUID) -> DiscountCode:
        await self._validate_property(property_id, tenant_id)
        data["property_id"] = property_id
        return await self.room_repo.create_discount_code(data)

    async def get_discount_codes(self, property_id: uuid.UUID, tenant_id: uuid.UUID) -> list[DiscountCode]:
        await self._validate_property(property_id, tenant_id)
        return await self.room_repo.get_discount_codes(property_id)
  