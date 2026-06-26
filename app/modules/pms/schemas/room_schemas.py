import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.pms.models.rooms_model import CancellationPolicy, RoomStatus


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class RoomTypeBase(BaseModel):
    hotel_detail_id: uuid.UUID = Field(
        ..., description="ID of the hotel detail associated with the room type"
    )
    room_type_name: str = Field(
        ...,
        description="Name of the room type",
        examples=["Standard", "Deluxe", "Suite", "Twin", "Double", "Single", "Custom"],
        min_length=2,
        max_length=100,
    )
    is_default: bool = Field(
        ..., description="Indicates if the room type is a default type or custom"
    )


class RoomTypeResponse(RoomTypeBase, TimestampSchema):
    id: uuid.UUID
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class BedTypeBase(BaseModel):
    hotel_detail_id: uuid.UUID = Field(
        ..., description="ID of the hotel detail associated with the bed type"
    )
    bed_name: str = Field(
        ...,
        description="Name of the bed type",
        examples=["King", "Queen", "Twin", "Double", "Single", "Custom"],
        min_length=2,
        max_length=100,
    )
    is_default: bool = Field(
        ..., description="Indicates if the bed type is a default type or custom"
    )


class BedTypeResponse(BedTypeBase, TimestampSchema):
    id: uuid.UUID
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class RoomPhotoBase(BaseModel):
    photo_url: str = Field(
        ...,
        description="URL of the room photo",
        examples=["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
    )


class RoomPhotoResponse(RoomPhotoBase, TimestampSchema):
    id: uuid.UUID
    room_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class RoomAmenityBase(BaseModel):
    amenity_id: uuid.UUID = Field(
        ..., description="ID of the amenity associated with the room"
    )


class RoomAmenityResponse(RoomAmenityBase, TimestampSchema):
    id: uuid.UUID
    room_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class RoomsBase(BaseModel):
    hotel_detail_id: uuid.UUID = Field(
        ..., description="ID of the hotel detail associated with the room"
    )
    floor_number: int = Field(
        ...,
        description="Floor number or identifier",
        examples=["0", "1", "2", "3", "4", "5"],
        ge=0,
        le=100,
    )
    max_adults: int = Field(
        ...,
        description="Maximum number of adults allowed in the room",
        examples=[1, 2, 3, 4],
        ge=1,
        le=30,
    )
    max_children: int = Field(
        ...,
        description="Maximum number of children allowed in the room",
        examples=[0, 1, 2, 3],
        ge=0,
        le=15,
    )
    base_rate: Decimal = Field(
        ...,
        description="Base rate for the room per night",
        examples=[100.00, 150.50, 200.75],
        ge=0,
    )
    status: RoomStatus = Field(
        ...,
        description="Current status of the room",
        examples=[
            RoomStatus.AVAILABLE,
            RoomStatus.DIRTY,
            RoomStatus.OCCUPIED,
            RoomStatus.MAINTENANCE,
            RoomStatus.OUT_OF_SERVICE,
        ],
    )
    cancellation_policy: CancellationPolicy = Field(
        ...,
        description="Cancellation policy for the room",
        examples=[
            CancellationPolicy.FLEXIBLE,
            CancellationPolicy.MODERATE,
            CancellationPolicy.STRICT,
            CancellationPolicy.NON_REFUNDABLE,
            CancellationPolicy.CUSTOM,
        ],
    )
    cancellation_notes: Optional[str] = Field(
        None,
        description="Additional notes regarding the cancellation policy",
        examples=[
            "No refunds for cancellations within 24 hours of check-in.",
            "Full refund if canceled at least 7 days before check-in.",
        ],
    )
    room_type: RoomTypeBase = Field(
        ..., description="Room types associated with the room"
    )
    bed_type: BedTypeBase = Field(..., description="Bed types associated with the room")
    photos: List[str] = Field(
        default_factory=list,
        description="List of urls photos  associated with the room",
    )
    amenities: List[uuid.UUID] = Field(
        default_factory=list,
        description="List of amenities ids associated with the room",
    )


class RoomsCreate(BaseModel):
    rooms: List[RoomsBase]


# class RoomsResponse(BaseModel):
#     id: uuid.UUID
#     room: RoomsBase
#     model_config = ConfigDict(from_attributes=True)


class RoomsResponseFlat(RoomsBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
