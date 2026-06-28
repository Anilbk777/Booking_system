import uuid

from app.modules.pms.models.rooms_model import (
    BedType,
    RoomAmenity,
    RoomPhoto,
    Rooms,
    RoomType,
)
from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.modules.pms.repositories.room_repo import RoomRepository
from app.modules.pms.schemas.room_schemas import RoomsCreate,RoomsDetailResponse
from app.utils.exceptions import (
    # HotelNotFoundException,
    PropertyNotFoundException,
    RepositoryException,
    RoomNameAlreadyExistsException,
    ServiceException,
    UnauthorizedException,
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

        # hotel_detail = await self.property_repo.get_hotel_detail_by_property_id(
        #     property_id=property_id, hotel_id=hotel_id
        # )
        # if not hotel_detail or hotel_detail.property_id != property_id:
        #     raise HotelNotFoundException("Hotel detail not found for this property")

        return property_obj

    async def create_rooms(
        self,
        property_id: uuid.UUID,
        tenant_id: uuid.UUID,
        payload: RoomsCreate,
    ):
        logger.info(f"[RoomService] Creating rooms for property {property_id}")
        try:
            property_obj = await self._validate_property(
                property_id, tenant_id
            )

            # from the models to prevent Pydantic models from converting into sub-dictionaries.
            rooms_data = []
            for room in payload.rooms:
                room_dict = room.model_dump(exclude={"photos", "amenities"})
                room_dict["photos"] = room.photos  # Keeps as clean list[str]
                room_dict["amenities"] = room.amenities  # Keeps as clean list[UUID]
                rooms_data.append(room_dict)

            # Delegate execution to the refactored loop method
            return await self.room_repo.create_rooms(
                rooms_data, hotel_id=property_obj.hotel_detail.id
            )

        except (
            PropertyNotFoundException,
            UnauthorizedException,
        ):
            logger.warning(
                "[RoomService] Validation rules failed before transaction initialization."
            )
            raise
        except (RoomNameAlreadyExistsException, RepositoryException):
            raise
        except Exception as e:
            logger.error(f"[RoomService] Error executing room creation batch: {str(e)}")
            raise ServiceException(str(e))


    async def get_all_rooms(self,property_id:uuid.UUID,tenant_id:uuid.UUID):
        logger.info(f"[RoomService] Fetching all rooms for property {property_id}")
        try:
            property_obj= await self._validate_property(property_id, tenant_id)
            rooms= await self.room_repo.get_all_rooms(hotel_id = property_obj.hotel_detail.id)
            
            rooms_data = []
            for room in rooms:
                formatted_room = {
                "id": room.id,
                "room_name": room.room_name,
                "floor_number": room.floor_number,
                "max_adults": room.max_adults,
                "max_children": room.max_children,
                "base_rate": room.base_rate,
                "status": room.status.value if hasattr(room.status, "value") else room.status,
                "cancellation_policy": room.cancellation_policy.value if hasattr(room.cancellation_policy, "value") else room.cancellation_policy,
                "cancellation_notes": room.cancellation_notes,
                
                # Directly map related objects
                "room_type": room.room_type, 
                "bed_type": room.bed_type,
                
                # Map lists cleanly
                "photos": [photo.photo_url for photo in room.room_photos],
                
                # Fetch full objects instead of just IDs
                "amenities": [
                    room_amenity.amenity 
                    for room_amenity in room.room_amenities 
                    if room_amenity.amenity is not None
                ]
            }
                
                # 4. Run through Pydantic to apply validations (like your base_rate validation)
                validated_data = RoomsDetailResponse.model_validate(formatted_room)
                rooms_data.append(validated_data.model_dump(mode="json"))
                
            return rooms_data
            
        except (PropertyNotFoundException,UnauthorizedException,RepositoryException):
            logger.warning(
                "[RoomService] Validation rules failed before transaction initialization."
            )
            raise
        except Exception as e:
            logger.error(f"[RoomService] Error executing room fetching: {str(e)}")
            raise ServiceException(str(e))

