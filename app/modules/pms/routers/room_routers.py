import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth.auth_middlewares import CurrentUser
from app.modules.pms.dependencies import get_room_service
from app.modules.pms.schemas.room_schemas import (
    BedTypeBase,
    RoomsBase,
    RoomsCreate,
    RoomsResponse,
    RoomTypeBase,
    RoomsDetailResponse,
    RoomsUpdate,
)

from app.modules.pms.services.room_services import RoomService
from app.utils.schemas import StandardResponse

router = APIRouter(prefix="/pms/properties", tags=["Rooms"])


@router.post(
    "/{property_id}/rooms",
    response_model=StandardResponse[list[RoomsResponse]],
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    property_id: uuid.UUID,
    room_data: RoomsCreate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to create a rooms. You should have a tenant.",
        )

    batch_results = await room_service.create_rooms(
        property_id=property_id,
        tenant_id=user.tenant_id,
        payload=room_data,
    )

    formatted_rooms = [
        RoomsResponse(
            id=item["room"].id,
            room=RoomsBase(
                hotel_detail_id=item["room"].hotel_detail_id,
                room_name=item["room"].room_name,
                floor_number=item["room"].floor_number,
                max_adults=item["room"].max_adults,
                max_children=item["room"].max_children,
                base_rate=item["room"].base_rate,
                status=item["room"].status,
                cancellation_policy=item["room"].cancellation_policy,
                cancellation_notes=item["room"].cancellation_notes,
                room_type=RoomTypeBase.model_validate(item["room_type"]),
                bed_type=BedTypeBase.model_validate(item["bed_type"]),
                photos=[photo.photo_url for photo in item["room_photos"]],
                amenities=[amenity.amenity_id for amenity in item["room_amenities"]],
            ),
        )
        for item in batch_results
    ]

    return {"success": True, "data": formatted_rooms}


@router.get(
    "/{property_id}/rooms",
    response_model=StandardResponse[list[RoomsDetailResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_rooms(
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to get rooms. You should have a tenant.",
        )
    rooms = await room_service.get_all_rooms(
        property_id=property_id, tenant_id=user.tenant_id
    )
    return {"success": True, "data": rooms}


@router.patch(
    "/{property_id}/rooms/{room_id}",
    response_model=StandardResponse[RoomsDetailResponse],
)
async def update_room(
    property_id: uuid.UUID,
    room_id: uuid.UUID,
    user: CurrentUser,
    room_data: RoomsUpdate,
    room_service: RoomService = Depends(get_room_service),
):
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to update a rooms. You should have a tenant.",
        )
    room = await room_service.update_room(
        property_id=property_id,
        tenant_id=user.tenant_id,
        room_id=room_id,
        payload=room_data,
    )
    return {"success": True, "data": room}


@router.delete("/{property_id}/rooms/{room_id}", response_model=StandardResponse[dict])
async def delete_room(
    property_id: uuid.UUID,
    room_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to delete a rooms. You should have a tenant.",
        )

    response = await room_service.delete_room(
        property_id=property_id,
        tenant_id=user.tenant_id,
        room_id=room_id,
    )

    return response
