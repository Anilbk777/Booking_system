from pydantic import field_validator
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
    room_type_name: str = Field(
        ...,
        title="Room Type Name",
        description="Name of the room type",
        examples=["Standard", "Deluxe", "Suite", "Twin", "Double", "Single"],
        min_length=2,
        max_length=100,
    )
    is_default: bool = Field(
        default=False,
        description="Indicates if the room type is a default type or custom",
    )
    model_config = ConfigDict(from_attributes=True)


class RoomTypeResponse(RoomTypeBase, TimestampSchema):
    id: uuid.UUID
    hotel_detail_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)


class BedTypeBase(BaseModel):
    bed_name: str = Field(
        ...,
        title="Bed Type Name",
        description="Name of the bed type",
        examples=["King", "Queen", "Twin", "Double", "Single"],
        min_length=2,
        max_length=100,
    )
    is_default: bool = Field(
        default=False,
        description="Indicates if the bed type is a default type or custom",
    )
    model_config = ConfigDict(from_attributes=True)


class BedTypeResponse(BedTypeBase, TimestampSchema):
    id: uuid.UUID
    hotel_detail_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)


class RoomsBase(BaseModel):
    room_name: str = Field(
        ...,
        title="Room Name",
        description="Unique identifier or number for this specific room record",
        examples=["101", "102", "Deluxe Suite A"],
        min_length=1,
        max_length=50,
    )
    floor_number: int = Field(
        ...,
        title="Floor Number",
        description="Floor number or identifier",
        ge=0,
        le=100,
    )
    max_adults: int = Field(
        ...,
        title="Maximum Number of Adults",
        description="Maximum number of adults allowed in the room",
        ge=1,
        le=30,
    )
    max_children: int = Field(
        ...,
        title="Maximum Number of Children",
        description="Maximum number of children allowed in the room",
        ge=0,
        le=15,
    )
    base_rate: Decimal = Field(
        ...,
        title="Base Rate",
        description="Base rate for the room per night",
        ge=0,
        le=100000,
    )
    status: RoomStatus = Field(
        RoomStatus.AVAILABLE,
        title="Status",
        description="Current status of the room (e.g. AVAILABLE, DIRTY, OCCUPIED)",
        examples=["AVAILABLE", "DIRTY", "OCCUPIED"],
    )
    cancellation_policy: CancellationPolicy = Field(
        CancellationPolicy.FLEXIBLE,
        title="Cancellation Policy",
        description="Cancellation policy for the room (e.g. FLEXIBLE, STRICT)",
        examples=["FLEXIBLE", "STRICT"],
    )
    cancellation_notes: Optional[str] = Field(
        None,
        title="Cancellation Notes",
        description="Additional notes regarding the cancellation policy",
        examples=["Cancellation is free up to 24 hours before check-in"],
    )
    room_type: RoomTypeBase = Field(
        ..., description="Room type characteristics associated with this room"
    )
    bed_type: BedTypeBase = Field(
        ..., description="Bed configuration profile associated with this room"
    )
    photos: List[str] = Field(
        default_factory=list,
        description="List of raw photo string URLs associated with the room",
    )
    amenities: List[uuid.UUID] = Field(
        default_factory=list,
        description="List of Amenity model UUID keys attached to this room",
    )

    # it must be greater than 0 and between 1 to 100000 base rate only
    @field_validator("base_rate", mode="before")
    @classmethod
    def validate_base_rate(cls, value: any) -> Decimal:
        try:
            value = Decimal(value)
            if value <= 0 or value > 100000:
                raise ValueError(
                    "must be greater than 0 and between 1 to 100000"
                )
            return value
        except ValueError:
            raise
        except Exception:
            raise ValueError("Base rate must be a valid number")


class RoomsCreate(BaseModel):
    rooms: List[RoomsBase] = Field(..., min_length=1)

class RoomsUpdate(BaseModel):
    room_name: Optional[str] = Field(
        ...,
        title="Room Name",
        description="Unique identifier or number for this specific room record",
        examples=["101", "102", "Deluxe Suite A"],
        min_length=1,
        max_length=50,
    )
    floor_number: Optional[int] = Field(
        ...,
        title="Floor Number",
        description="Floor number or identifier",
        ge=0,
        le=100,
    )
    max_adults: Optional[int] = Field(
        ...,
        title="Maximum Number of Adults",
        description="Maximum number of adults allowed in the room",
        ge=1,
        le=30,
    )
    max_children: Optional[int] = Field(
        ...,
        title="Maximum Number of Children",
        description="Maximum number of children allowed in the room",
        ge=0,
        le=15,
    )
    base_rate: Optional[Decimal] = Field(
        ...,
        title="Base Rate",
        description="Base rate for the room per night",
        ge=0,
        le=100000,
    )
    status: Optional[RoomStatus] = Field(
        RoomStatus.AVAILABLE,
        title="Status",
        description="Current status of the room (e.g. AVAILABLE, DIRTY, OCCUPIED)",
        examples=["AVAILABLE", "DIRTY", "OCCUPIED"],
    )
    cancellation_policy: Optional[CancellationPolicy] = Field(
        CancellationPolicy.FLEXIBLE,
        title="Cancellation Policy",
        description="Cancellation policy for the room (e.g. FLEXIBLE, STRICT)",
        examples=["FLEXIBLE", "STRICT"],
    )
    cancellation_notes: Optional[str] = Field(
        None,
        title="Cancellation Notes",
        description="Additional notes regarding the cancellation policy",
        examples=["Cancellation is free up to 24 hours before check-in"],
    )
    room_type: Optional[RoomTypeBase] = Field(
        ..., description="Room type characteristics associated with this room"
    )
    bed_type: Optional[BedTypeBase] = Field(
        ..., description="Bed configuration profile associated with this room"
    )
    photos: Optional[List[str]] = Field(
        default_factory=list,
        description="List of raw photo string URLs associated with the room",
    )
    amenities: Optional[List[uuid.UUID]] = Field(
        default_factory=list,
        description="List of Amenity model UUID keys attached to this room",
    )


class RoomsResponse(BaseModel):
    id: uuid.UUID
    room: RoomsBase
    model_config = ConfigDict(from_attributes=True)


class AmenityDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_default: bool
    
    model_config = ConfigDict(from_attributes=True)



class RoomsDetailResponse(BaseModel):
    id: uuid.UUID
    room_name: str 
    floor_number: int 
    max_adults: int 
    max_children: int 
    base_rate: Decimal
    status: str
    cancellation_policy: str
    cancellation_notes: Optional[str]
    room_type: RoomTypeBase
    bed_type: BedTypeBase
    photos: List[str]
    amenities: List[AmenityDetailResponse]
    model_config = ConfigDict(from_attributes=True)


