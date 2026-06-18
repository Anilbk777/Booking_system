from fastapi import APIRouter, Depends, status
from app.modules.pms.schemas.room_schemas import RoomTypeCreate, RoomTypeResponse
from app.modules.pms.services.room_services import RoomService
from app.modules.pms.dependencies import get_room_service
from app.modules.auth.auth_middlewares import CurrentUser
import uuid

router = APIRouter(prefix="/pms/properties", tags=["Rooms"])


@router.post(
    "/{property_id}/room-types",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_type(
    property_id: uuid.UUID,
    room_type: RoomTypeCreate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.create_room_type(
        room_type_data=room_type.model_dump(),
        tenant_id=user.tenant_id,
        property_id=property_id,
    )


@router.get(
    "/{property_id}/room-types",
    response_model=list[RoomTypeResponse],
    status_code=status.HTTP_200_OK,
)
async def get_room_types(
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_room_types(user.tenant_id, property_id)
