from app.modules.pms.repositories.room_units_repo import RoomUnitRepository
from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.modules.pms.models.rooms_model import PropertyRoomUnit
from app.utils.exceptions import ServiceException, PropertyNotFoundException, UnauthorizedException
from app.utils.logging import LoggerFactory
import uuid

logger = LoggerFactory.get_logger(__name__)

class RoomUnitService:
    def __init__(self, room_unit_repo: RoomUnitRepository, property_repo: PropertyRepository):
        self.room_unit_repo = room_unit_repo
        self.property_repo = property_repo

    async def _validate_property(self, property_id: uuid.UUID, tenant_id: uuid.UUID):
        property_obj = await self.property_repo.get_property_by_id(property_id, tenant_id)
        if not property_obj:
            raise PropertyNotFoundException("Property not found")
        if property_obj.tenant_id != tenant_id:
            raise UnauthorizedException("unauthorized")
        return property_obj

    async def create_room_unit(self, data: dict, property_id: uuid.UUID, tenant_id: uuid.UUID) -> PropertyRoomUnit:
        await self._validate_property(property_id, tenant_id)
        data["property_id"] = property_id
        return await self.room_unit_repo.create_room_unit(data)

    async def get_room_units(self, property_id: uuid.UUID, tenant_id: uuid.UUID, room_type_id: uuid.UUID = None) -> list[PropertyRoomUnit]:
        await self._validate_property(property_id, tenant_id)
        return await self.room_unit_repo.get_room_units(property_id, room_type_id)

    async def get_room_unit_by_id(self, unit_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID) -> PropertyRoomUnit:
        await self._validate_property(property_id, tenant_id)
        unit = await self.room_unit_repo.get_room_unit_by_id(unit_id)
        if not unit or unit.property_id != property_id:
            raise ServiceException("Room unit not found")
        return unit

    async def update_room_unit(self, unit_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID, data: dict) -> PropertyRoomUnit:
        await self._validate_property(property_id, tenant_id)
        unit = await self.room_unit_repo.get_room_unit_by_id(unit_id)
        if not unit or unit.property_id != property_id:
            raise ServiceException("Room unit not found or unauthorized")
        return await self.room_unit_repo.update_room_unit(unit_id, data)

    async def delete_room_unit(self, unit_id: uuid.UUID, property_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        await self._validate_property(property_id, tenant_id)
        unit = await self.room_unit_repo.get_room_unit_by_id(unit_id)
        if not unit or unit.property_id != property_id:
            raise ServiceException("Room unit not found or unauthorized")
        return await self.room_unit_repo.delete_room_unit(unit_id)
