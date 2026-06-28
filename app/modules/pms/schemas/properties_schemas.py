import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Annotated, Any, List, Optional

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    WithJsonSchema,
    field_validator,
    model_validator,
)

from app.modules.pms.models.properties_model import PropertyType


# ---------------------------------------------------------
# Custom AM/PM Time Parser & Serializer Using Annotated
# ---------------------------------------------------------
def parse_ampm_string_to_time(v: Any) -> time:
    if isinstance(v, time):
        return v
    if isinstance(v, str):
        cleaned_time = v.strip().upper()
        for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
            try:
                return datetime.strptime(cleaned_time, fmt).time()
            except ValueError:
                continue
    raise ValueError(
        "Invalid time format. Please provide a value in format like '9:00 AM' or '12:00 PM'"
    )


def serialize_time_to_ampm_string(t: time) -> str:
    formatted = t.strftime("%I:%M %p")
    if formatted.startswith("0"):
        formatted = formatted[1:]
    return formatted


Time12Hour = Annotated[
    time,
    BeforeValidator(parse_ampm_string_to_time),
    PlainSerializer(serialize_time_to_ampm_string, return_type=str, when_used="always"),
    WithJsonSchema(
        {
            "type": "string",
            "format": "time",
            "examples": ["9:00 AM", "12:30 PM"],
            "description": "Time string in 12-hour AM/PM format",
        }
    ),
]

# ---------------------------------------------------------
# Core Schema Implementations
# ---------------------------------------------------------


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class PropertyPhotoResponse(TimestampSchema):
    id: uuid.UUID
    property_id: uuid.UUID
    photo_url: str
    model_config = ConfigDict(from_attributes=True)


class PropertyHotelDetailBase(BaseModel):
    check_in_time_from: Time12Hour
    check_in_time_to: Time12Hour
    check_out_time_from: Time12Hour
    check_out_time_to: Time12Hour
    total_rooms: int = Field(default=1, ge=1, title="Total Rooms", description="Total number of rooms")
    year_built: Optional[int] = Field(None, ge=1800, le=2100, title="Year Built", description="Year when the property was built")
    number_of_floors: int = Field(default=1, ge=1, title="Number of Floors", description="Number of floors in the property")

    @model_validator(mode="after")
    def validate_time_sequences(self) -> "PropertyHotelDetailBase":
        if self.check_in_time_from >= self.check_in_time_to:
            raise ValueError("check_in_time_from cannot be later than check_in_time_to")
        if self.check_out_time_from >= self.check_out_time_to:
            raise ValueError(
                "check_out_time_from cannot be later than check_out_time_to"
            )
        return self


class PropertyHotelDetailResponse(PropertyHotelDetailBase, TimestampSchema):
    id: uuid.UUID
    property_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class AmenityBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, title="Amenity Name", description="Name of the amenity")
    is_default: bool = Field(default=False)


class AmenityResponse(AmenityBase, TimestampSchema):
    id: uuid.UUID
    property_id: Optional[uuid.UUID] = None  # Properly typed for checking
    model_config = ConfigDict(from_attributes=True)


class PropertyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, title="Property Name", description="Name of the property")
    type: PropertyType = Field(default=PropertyType.HOTEL)
    description: Optional[str] = Field(None, max_length=2000, title="Description", description="Description of the property")
    country: str = Field(..., min_length=2, max_length=100, title="Country", description="Country of the property")
    state: str = Field(..., min_length=2, max_length=100, title="State", description="State of the property")
    city: str = Field(..., min_length=2, max_length=100, title="City", description="City of the property")
    zip_code: str = Field(..., min_length=2, max_length=10, title="Zip Code", description="Zip code of the property")
    address: str = Field(..., min_length=2, max_length=255, title="Address", description="Address of the property")
    latitude: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6, title="Latitude", description="Latitude of the property")
    longitude: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6, title="Longitude", description="Longitude of the property")


class PropertyCreate(PropertyBase):
    model_config = ConfigDict(str_strip_whitespace=True)
    hotel_detail: PropertyHotelDetailBase
    amenities: List[AmenityBase] = Field(default_factory=list)
    photo_urls: List[str] = Field(default_factory=list)


    @field_validator("amenities")
    @classmethod
    def validate_amenities(cls, v: List[AmenityBase]) -> List[AmenityBase]:
        """Validate amenities and raise error on duplicates."""
        if not v:
            return []

        seen = set()
        unique_amenities = []
        duplicates = []

        for amenity in v:
            # Strip whitespace
            clean_name = amenity.name.strip()

            # Skip empty strings
            if not clean_name:
                continue

            # Case-insensitive check
            normalized = clean_name.lower()

            if normalized not in seen:
                seen.add(normalized)
                unique_amenities.append(amenity)
            else:
                duplicates.append(amenity)

        if duplicates:
            raise ValueError(
                f"Duplicate amenities found: {', '.join(set([a.name for a in duplicates]))}. "
                f"Please remove duplicates before submitting."
            )

        return unique_amenities


class PropertyResponse(PropertyBase, TimestampSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    hotel_detail: PropertyHotelDetailResponse
    photos: List[PropertyPhotoResponse] = Field(default_factory=list)
    amenities: List[AmenityResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


# return response with property details only
class PropertyDetailResponse(PropertyBase, TimestampSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)



class DefaultAmenityResponse(BaseModel):
    id: uuid.UUID = Field(..., description="The unique identifier of the default amenity")
    name: str = Field(..., description="The display name of the default amenity")
    is_default: bool = Field(..., description="Flag indicating if this is a global system default")

    # Enforce Pydantic V2 to safely parse from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)
