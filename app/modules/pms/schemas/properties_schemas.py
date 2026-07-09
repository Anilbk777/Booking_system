import uuid
import uuid
import re
from datetime import datetime, time, date, timedelta
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
    EmailStr,
)

from app.modules.pms.models.properties_model import PropertyType

MAX_IMAGES_PER_PROPERTY = 20

class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GeneralPropertyInfo(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        title="Property Name",
        description="Name of the property",
    )
    type: PropertyType = Field(
        ...,
        title= "property type",
        default=PropertyType.HOTEL,
        description="Type of the property"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        title="Description",
        description="Description of the property",
    )
    total_rooms: int = Field(
        default=1,
        ge=1,
        le=10000,
        title="Total Rooms",
        description="Total number of rooms"
    )
    year_built: Optional[int] = Field(
        None,
        ge=1800,
        le=2100,
        title="Year Built",
        description="Year when the property was built",
    )
    number_of_floors: int = Field(
        default=1,
        ge=1,
        le=1000,
        title="Number of Floors",
        description="Number of floors in the property",
    )

    phone_number:str = Field(
        ...,
        min_length=10,
        max_length=10,
        title="Phone Number",
        description="Phone number of the property owner for the property",
    )
    email:EmailStr = Field(
        ...,
        title="Email",
        description="Email of the property owner for the property",
    )

    @field_validator("phone_number")
    @classmethod
    def verify_phone_number(cls, value:str) -> str:
        value = value.strip()
        if " " in value:
            raise ValueError("Phone number must not contain spaces.")
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits.")
        if len(value) != 10:
            raise ValueError("Phone number must be 10 digits.")
        return value

    @field_validator("name")
    @classmethod
    def clean_and_verify_name(cls, value:str) -> str:
        value = value.strip()
        if not re.match(r"^[a-zA-Z\s]+$", value):
            raise ValueError("Name must contain only alphabetic characters and spaces")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def pre_strip_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value    


class GeneralPropertyInfoResponse(GeneralPropertyInfo,TimestampSchema):
    id: uuid.UUID

class Location(BaseModel):
    country: str = Field(
        ...,
        min_length=2,
        max_length=100,
        title="Country",
        description="Country of the property",
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        title="State",
        description="State of the property",
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        title="City",
        description="City of the property",
    )
    zip_code: str = Field(
        ...,
        min_length=2,
        max_length=10,
        title="Zip Code",
        description="Zip code of the property",
    )
    address: str = Field(
        ...,
        min_length=2,
        max_length=255,
        title="Address",
        description="Address of the property",
    )
    latitude: Optional[Decimal] = Field(
        None,
        max_digits=9,
        decimal_places=6,
        title="Latitude",
        description="Latitude of the property",
    )
    longitude: Optional[Decimal] = Field(
        None,
        max_digits=9,
        decimal_places=6,
        title="Longitude",
        description="Longitude of the property",
    )


class LocationResponse(Location):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class CustomAmenityItem(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the custom amenity")
    icon: Optional[str] = Field(None, max_length=50, description="Icon code (e.g. 'fa-wifi')")

class PhotoCollection(BaseModel):
    cover: Optional[HttpUrl] = Field(
        None, 
        description="The primary cover image URL. If None, no cover is set."
    )
    gallery: List[HttpUrl] = Field(
        default_factory=list, 
        description="List of secondary image URLs."
    )

    @model_validator(mode='after')
    def validate_gallery_limit(self):
        # Optional: Prevent users from uploading 500 images and crashing your UI
        if len(self.gallery) > 20:
            raise ValueError("Gallery cannot contain more than 20 images.")
        return self

class PropertyAmenity(BaseModel):
    system_amenity_ids: List[uuid.UUID] = Field(
        default_factory=list, 
        description="List of system-provided amenity IDs"
    )
    custom_amenities: List[CustomAmenityItem] = Field(
        default_factory=list, 
        description="List of user-defined custom amenities"
    )

class PropertyPhotosAndAmenities(BaseModel):
    photos: PhotoCollection = Field(default_factory=PhotoCollection)
    amenities: PropertyAmenity = Field(default_factory=PropertyAmenity)


class PropertyPhotosAndAmenitiesResponse(PropertyPhotosAndAmenities):
    id:uuid.UUID
    model_config = ConfigDict(from_attributes=True)




class Propertylocalization(BaseModel):
    currency:str =Field(
        ...,
        min_length=3,
        max_length=20,
        title="Currency",
        description="Currency of the property",
    )
    timezone: str = Field(
        default="UTC",
        min_length=3,
        max_length=100,
        title="Timezone",
        description="Timezone of the tenant",
    )

    language:str =Field(
        ...,
        min_length=2,
        max_length=50,
        title="Language",
        description="Language of the property",
    )

    check_in_time:str =Field(
        ...,
        min_length=8,
        max_length=8,
        title="Check In Time",
        description="Check in time of the property",
    )

    check_out_time:str =Field(
        ...,
        min_length=5,
        max_length=5,
        title="Check Out Time",
        description="Check out time of the property",
    )
    check_in_grace_period:int =Field(
        default=0,
        le=60,
        ge=0
        title="Check In Grace Period",
        description="Check in grace period of the property",
    )

    check_out_grace_period:int =Field(
        default=0,
        le=60,
        ge=0
        title="Check Out Grace Period",
        description="Check out grace period of the property",
    )
    
    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
            return value
        except Exception:
            raise ValueError(
                f"'{value}' is not a valid IANA timezone name (e.g., 'Asia/Kathmandu')"
            )

class PropertylocalizationResponse(Propertylocalization):
    id: uuid.UUID
    model_config= ConfigDict(from_attributes=True)

class BrandVisual(BaseModel):
    brand_logo_url:str = Field(
        None,
        max_length=2048,
        title="Brand Logo URL",
        description="URL of the brand logo",
    )
    brand_color:str = Field(
        None,
        min_length=3,
        max_length=7,
        title="Brand Color",
        description="Color of the brand",
    )

class BrandVisualResponse(BrandVisual):
    id: uuid.UUID
    model_config=ConfigDict(from_attributes=True)

# # ---------------------------------------------------------
# # Custom AM/PM Time Parser & Serializer Using Annotated
# # ---------------------------------------------------------
# def parse_ampm_string_to_time(v: Any) -> time:
#     if isinstance(v, time):
#         return v
#     if isinstance(v, str):
#         cleaned_time = v.strip().upper()
#         for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
#             try:
#                 return datetime.strptime(cleaned_time, fmt).time()
#             except ValueError:
#                 continue
#     raise ValueError(
#         "Invalid time format. Please provide a value in format like '9:00 AM' or '12:00 PM'"
#     )


# def serialize_time_to_ampm_string(t: time) -> str:
#     formatted = t.strftime("%I:%M %p")
#     if formatted.startswith("0"):
#         formatted = formatted[1:]
#     return formatted


# Time12Hour = Annotated[
#     time,
#     BeforeValidator(parse_ampm_string_to_time),
#     PlainSerializer(serialize_time_to_ampm_string, return_type=str, when_used="json"),
#     WithJsonSchema(
#         {
#             "type": "string",
#             "format": "time",
#             "examples": ["9:00 AM", "12:30 PM"],
#             "description": "Time string in 12-hour AM/PM format",
#         }
#     ),
# ]

# ---------------------------------------------------------
# Core Schema Implementations
# ---------------------------------------------------------




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
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        title="Amenity Name",
        description="Name of the amenity",
    )
    is_default: bool = Field(default=False)


class AmenityResponse(AmenityBase, TimestampSchema):
    id: uuid.UUID
    property_id: Optional[uuid.UUID] = None  # Properly typed for checking
    model_config = ConfigDict(from_attributes=True)


class PropertyBase(BaseModel):
    
    country: str = Field(
        ...,
        min_length=2,
        max_length=100,
        title="Country",
        description="Country of the property",
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        title="State",
        description="State of the property",
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        title="City",
        description="City of the property",
    )
    zip_code: str = Field(
        ...,
        min_length=2,
        max_length=10,
        title="Zip Code",
        description="Zip code of the property",
    )
    address: str = Field(
        ...,
        min_length=2,
        max_length=255,
        title="Address",
        description="Address of the property",
    )
    latitude: Optional[Decimal] = Field(
        None,
        max_digits=9,
        decimal_places=6,
        title="Latitude",
        description="Latitude of the property",
    )
    longitude: Optional[Decimal] = Field(
        None,
        max_digits=9,
        decimal_places=6,
        title="Longitude",
        description="Longitude of the property",
    )


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

    @field_validator("photo_urls")
    @classmethod
    def validate_photo_urls(cls, v: List[str]) -> List[str]:
        """Validate photo urls and raise error on duplicates."""
        if not v:
            return []

        seen = set()
        unique_photo_urls = []
        duplicates = []

        if len(v) > MAX_IMAGES_PER_PROPERTY:
            raise ValueError(
                f"Exceeded maximum number of images allowed: {MAX_IMAGES_PER_PROPERTY}"
            )

        for photo_url in v:
            # Strip whitespace
            clean_photo_url = photo_url.strip()

            # Skip empty strings
            if not clean_photo_url:
                continue

            # Case-insensitive check
            normalized = clean_photo_url.lower()

            if normalized not in seen:
                seen.add(normalized)
                unique_photo_urls.append(photo_url)
            else:
                duplicates.append(photo_url)

        if duplicates:
            raise ValueError(
                f"Duplicate photo urls found: {', '.join(set([a.photo_url for a in duplicates]))}. "
                f"Please remove duplicates before submitting."
            )

        return unique_photo_urls


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
    id: uuid.UUID = Field(
        ..., description="The unique identifier of the default amenity"
    )
    name: str = Field(..., description="The display name of the default amenity")
    is_default: bool = Field(
        ..., description="Flag indicating if this is a global system default"
    )

    # Enforce Pydantic V2 to safely parse from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)


class PropertySearchQueryParams(BaseModel):
    destination: str = Field(
        ...,
        description="Search by name, country, state, city, or address",
        max_length=100,
    )
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    adults: int = Field(default=1, ge=1, le=30, description="Number of adults")
    children: int = Field(default=0, ge=0, le=15, description="Number of children")
    room_count: int = Field(
        default=1, ge=1, le=30, description="Minimum available rooms required"
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "PropertySearchQueryParams":
        self.destination = self.destination.strip().lower()
        check_in = self.check_in
        check_out = self.check_out
        today = date.today()
        if check_out <= check_in:
            raise ValueError("check out must be after check in")
        if check_in < today:
            raise ValueError("check in must be after today")
        if check_out > today + timedelta(days=365 * 3):
            raise ValueError("check out must be within three years from today")
        return self


class PropertySearchResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    price: Decimal
    address: str
    city: str
    state: str
    country: str   
    photo_url: Optional[str | None] = Field(default=None)


    model_config = ConfigDict(from_attributes=True)
