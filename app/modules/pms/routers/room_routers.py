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
)

from app.modules.pms.services.room_services import RoomService
from app.utils.schemas import StandardResponse

router = APIRouter(prefix="/pms/properties", tags=["Rooms"])


@router.post(
    "/{property_id}/rooms",
    response_model=StandardResponse[
        list[RoomsResponse]
    ],  # Ensures auto-docs list serialization
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

    # FIX: Pass the raw Pydantic payload directly instead of calling .model_dump()
    # This preserves the strong type definitions for primitive fields (like list[UUID] for amenities)
    batch_results = await room_service.create_rooms(
        property_id=property_id,
        tenant_id=user.tenant_id,
        payload=room_data,
    )

    # 2. Iterate through the array of saved records to build the structured response objects
    formatted_rooms = [
        RoomsResponse(
            id=item["room"].id,
            room=RoomsBase(
                hotel_detail_id=item["room"].hotel_detail_id,
                room_name=item[
                    "room"
                ].room_name,  # Handled the unique room name property
                floor_number=item["room"].floor_number,
                max_adults=item["room"].max_adults,  # Lowercase mapping alignment
                max_children=item["room"].max_children,
                base_rate=item["room"].base_rate,
                status=item["room"].status,
                cancellation_policy=item["room"].cancellation_policy,
                cancellation_notes=item["room"].cancellation_notes,
                # Model validation parses SQLAlchemy objects to Pydantic schemas cleanly
                room_type=RoomTypeBase.model_validate(item["room_type"]),
                bed_type=BedTypeBase.model_validate(item["bed_type"]),
                # Extract clean flat primitive arrays for lists
                photos=[photo.photo_url for photo in item["room_photos"]],
                amenities=[amenity.amenity_id for amenity in item["room_amenities"]],
            ),
        )
        for item in batch_results
    ]

    # 3. Return the entire multi-room data structure packed inside your standardized envelope format
    return {"success": True, "data": formatted_rooms}


@router.get("/{property_id}/rooms", response_model=StandardResponse[
        list[RoomsDetailResponse]
    ],
    status_code=status.HTTP_200_OK
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
    rooms = await room_service.get_all_rooms(property_id=property_id, tenant_id=user.tenant_id)
    return {
        "success":True,
        "data": rooms
    }