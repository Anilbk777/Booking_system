from app.modules.pms.schemas.room_schemas import RoomTypeCreate
import uuid

from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.modules.pms.repositories.room_repo import RoomRepository
from app.modules.pms.schemas.room_schemas import (

    RoomBulkCreateRequest,
    RoomBulkCreateResponse,
    RoomResponse,
    RoomTypeResponse,
    BedTypeResponse,
    RoomTypeCreate,
    BedTypeCreate,
)
from app.utils.exceptions import (
    PropertyNotFoundException,
    RepositoryException,
    RoomTypeAlreadyExistsException,
    BedTypeAlreadyExistsException,
    RoomNameAlreadyExistsException,
    ServiceException,
    UnauthorizedException,
    RoomNotFoundException,
    AmenityNotFoundException,
    InvalidImageException,
    ImageStorageException,
)
from app.utils.logging import LoggerFactory

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

    async def _validate_room_bed_and_type(self,property_id:uuid.UUID, room_types:list[str], bed_types:list[str]):

        for room_type in room_types:
            room_type_obj = await self.room_repo.get_existing_room_type_name(
                property_id, room_type
            )
            if room_type_obj:
                raise RoomTypeAlreadyExistsException("Room type name already exists")

        for bed_type in bed_types:
            bed_type_obj = await self.room_repo.get_exisiting_bed_type_name(
                property_id, bed_type
            )
            if bed_type_obj:
                raise BedTypeAlreadyExistsException("Bed type name already exists")

    async def create_rooms(
        self,
        property_id: uuid.UUID,
        tenant_id: uuid.UUID,
        payload: RoomBulkCreateRequest,
    ) -> RoomBulkCreateResponse:
        logger.info(f"[RoomService] Creating rooms for property {property_id}")
        try:
            property_obj = await self._validate_property(property_id, tenant_id)
            payload_dict = payload.model_dump()
            rooms_data = payload_dict["rooms"]
            logger.info(f"[RoomService] Rooms data: {rooms_data}")

            created_rooms = await self.room_repo.create_rooms(property_obj.id, rooms_data) 
            return RoomBulkCreateResponse(
                rooms=[
                    RoomResponse.model_validate(r) for r in created_rooms
                ])
        except (
            PropertyNotFoundException,
            UnauthorizedException,
            RoomNameAlreadyExistsException,
            RepositoryException,
            InvalidImageException,
            ImageStorageException,
        ):
            raise
        except Exception as e:
            logger.error(f"[RoomService] Error executing room creation batch: {str(e)}")
            raise ServiceException(str(e))

    async def create_room_type(self, property_id:uuid.UUID, tenant_id:uuid.UUID,payload:RoomTypeCreate) -> RoomTypeResponse:
        logger.info(f"[RoomService] creating room type for property {property_id}")
        try:
            property_obj = await self._validate_property(property_id, tenant_id)
            room_type_dict = payload.model_dump()
            existing_room_type_name = await self.room_repo.get_exisitng_room_type_name(property_id, room_type_dict["room_type_name"])
            if existing_room_type_name:
                logger.info(f"[RoomService] Room type name already exists: {room_type_dict['room_type_name']}")
                raise RoomTypeAlreadyExistsException("Room type name already exists")
            created_room_type = await self.room_repo.create_room_type(property_obj.id, room_type_dict)
            return RoomTypeResponse.model_validate(created_room_type)    
        
        except (RoomTypeAlreadyExistsException, RepositoryException):
            raise
        except Exception as e:
            logger.error(f"[RoomService] Error executing room type creation: {str(e)}")
            raise ServiceException(str(e))
    
    async def create_bed_type(self, property_id:uuid.UUID, tenant_id:uuid.UUID, payload:BedTypeCreate) -> BedTypeResponse:
        logger.info(f"[RoomService] creating bed type for property {property_id}")
        try:
            property_obj = await self._validate_property(property_id, tenant_id)
            bed_type_dict = payload.model_dump()
            existing_bed_type_name = await self.room_repo.get_exisiting_bed_type_name(property_id, bed_type_dict["bed_name"])
            if existing_bed_type_name:
                logger.info(f"[RoomService] Bed type name already exists: {bed_type_dict['bed_name']}")
                raise BedTypeAlreadyExistsException("Bed type name already exists")
            created_bed_type = await self.room_repo.create_bed_type(property_obj.id, bed_type_dict)
            return BedTypeResponse.model_validate(created_bed_type)    
        
        except (BedTypeAlreadyExistsException, RepositoryException):
            raise
        except Exception as e:
            logger.error(f"[RoomService] Error executing bed type creation: {str(e)}")
            raise ServiceException(str(e))