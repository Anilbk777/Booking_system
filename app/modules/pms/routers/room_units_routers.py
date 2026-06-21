from fastapi import APIRouter, Depends, status
from app.modules.pms.schemas.room_units_schemas import (
    RoomUnitCreate,
    RoomUnitUpdate,
    RoomUnitResponse,
)
from app.modules.pms.services.room_units_services import RoomUnitService
from app.modules.pms.dependencies import get_room_unit_service
from app.modules.auth.auth_middlewares import CurrentUser
import uuid

router = APIRouter(prefix="/pms/properties", tags=["Room Units"])

@router.post(
    "/{property_id}/room-units",
    response_model=RoomUnitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_unit(
    property_id: uuid.UUID,
    room_unit: RoomUnitCreate,
    user: CurrentUser,
    room_unit_service: RoomUnitService = Depends(get_room_unit_service),
):
    return await room_unit_service.create_room_unit(
        room_unit.model_dump(), property_id, user.tenant_id
    )

@router.get(
    "/{property_id}/room-units",
    response_model=list[RoomUnitResponse],
)
async def get_room_units(
    property_id: uuid.UUID,
    user: CurrentUser,
    room_type_id: uuid.UUID = None,
    room_unit_service: RoomUnitService = Depends(get_room_unit_service),
):
    return await room_unit_service.get_room_units(property_id, user.tenant_id, room_type_id)

@router.get(
    "/{property_id}/room-units/{unit_id}",
    response_model=RoomUnitResponse,
)
async def get_room_unit(
    property_id: uuid.UUID,
    unit_id: uuid.UUID,
    user: CurrentUser,
    room_unit_service: RoomUnitService = Depends(get_room_unit_service),
):
    return await room_unit_service.get_room_unit_by_id(unit_id, property_id, user.tenant_id)

@router.put(
    "/{property_id}/room-units/{unit_id}",
    response_model=RoomUnitResponse,
)
async def update_room_unit(
    property_id: uuid.UUID,
    unit_id: uuid.UUID,
    room_unit_data: RoomUnitUpdate,
    user: CurrentUser,
    room_unit_service: RoomUnitService = Depends(get_room_unit_service),
):
    return await room_unit_service.update_room_unit(
        unit_id, property_id, user.tenant_id, room_unit_data.model_dump(exclude_unset=True)
    )

@router.delete("/{property_id}/room-units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_unit(
    property_id: uuid.UUID,
    unit_id: uuid.UUID,
    user: CurrentUser,
    room_unit_service: RoomUnitService = Depends(get_room_unit_service),
):
    await room_unit_service.delete_room_unit(unit_id, property_id, user.tenant_id)
    return None
