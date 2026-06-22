import uuid
from decimal import Decimal
from datetime import datetime, time
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import (
    BaseModel,
    Field,
    BeforeValidator,
    PlainSerializer,
    ConfigDict,
    WithJsonSchema,
)


# ---------------------------------------------------------
# Custom AM/PM Time Parser & Serializer Using Annotated
# ---------------------------------------------------------
def parse_ampm_string_to_time(v: any) -> time:
    """Parses incoming frontend strings like '9:00 AM' or '12:30 PM' into a Python time object."""
    if isinstance(v, time):
        return v
    if isinstance(v, str):
        cleaned_time = v.strip().upper()
        # Fallbacks for standard 12-hour variations or 24-hour inputs
        for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
            try:
                return datetime.strptime(cleaned_time, fmt).time()
            except ValueError:
                continue
    raise ValueError(
        "Invalid time format. Please provide a value in format like '9:00 AM' or '12:00 PM'"
    )


def serialize_time_to_ampm_string(t: time) -> str:
    """Serializes an internal Python time object back into an clean '9:00 AM' string format."""
    formatted = t.strftime("%I:%M %p")
    # Clean leading zeroes for aesthetic compliance (e.g., "09:00 AM" -> "9:00 AM")
    if formatted.startswith("0"):
        formatted = formatted[1:]
    return formatted

    # Type reusable across all your schemas


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


class PropertyBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=2, max_length=255)
    type: str = Field(default="Hotel", min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    country: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    zip_code: str = Field(..., min_length=2, max_length=10)
    address: str = Field(..., min_length=2, max_length=255)
    latitude: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6)
    longitude: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6)
    check_in_time_from: Time12Hour
    check_in_time_to:Time12Hour
    check_out_time_from: Time12Hour
    check_out_time_to: Time12Hour
    number_of_floors: int = Field(default=1, ge=1)
    total_rooms: int = Field(default=0, ge=0)
    year_built: Optional[int] = Field(None, ge=1000, le=2100)
    amenities: Optional[List[str]] = Field(default=None)


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    type: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=2, max_length=10)
    address: Optional[str] = Field(None, min_length=2, max_length=255)
    latitude: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6)
    longitude: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6)
    check_in_time_from:  Optional[Time12Hour] = None
    check_in_time_to: Optional[Time12Hour] = None
    check_out_time_from: Optional[Time12Hour] = None
    check_out_time_to: Optional[Time12Hour] = None
    number_of_floors: Optional[int] = Field(None, ge=1)
    total_rooms: Optional[int] = Field(None, ge=0)
    year_built: Optional[int] = Field(None, ge=1000, le=2100)
    amenities: Optional[List[str]] = Field(default=None)


class PropertyResponse(PropertyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyPhotoResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    photo_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
