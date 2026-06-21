from pydantic import BaseModel, Field, ConfigDict, field_validator
import uuid
from typing import Optional, List
from datetime import time, datetime
from app.modules.pms.models.properties_model import PropertyType, AmenityType


class PropertyBase(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=100, description="Name of the property"
    )
    type: PropertyType = Field(..., description="Type of the property")
    country: str = Field(..., description="Country of the property")
    state: str = Field(..., description="State of the property")
    city: str = Field(..., description="City of the property")
    zip_code: str = Field(..., description="Zip code of the property")
    address: str = Field(..., description="Address of the property")
    lat: Optional[float] = Field(None, description="Latitude of the property")
    lng: Optional[float] = Field(None, description="Longitude of the property")
    star_rating: Optional[int] = Field(None, description="Star rating of the property")
    description: Optional[str] = Field(None, description="Detailed description of the property")
    is_active: bool = Field(default=True, description="Whether the property is active")

    check_in_time: Optional[time] = Field(
        default=time(14, 00), description="Check-in time of the property"
    )
    check_out_time: Optional[time] = Field(
        default=time(12, 00), description="Check-out time of the property"
    )

    @field_validator("check_in_time", "check_out_time")
    @classmethod
    def validate_check_in_out_time(cls, v: Optional[time]) -> Optional[time]:
        if v is not None and not (time(0, 0) <= v <= time(23, 59)):
            raise ValueError(
                "Check-in and check-out time must be between 00:00 and 23:59"
            )
        return v


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    type: Optional[PropertyType] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    star_rating: Optional[int] = None
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PropertyResponse(PropertyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyAmenityBase(BaseModel):
    amenity: List[AmenityType] = Field(
        default_factory=list,
        description="List of amenities in the property. Can be empty.",
        examples=[["Pool", "Gym", "Parking"]],
    )


class PropertyAmenityCreate(PropertyAmenityBase):
    pass


class PropertyAmenityResponse(PropertyAmenityBase):
    id: uuid.UUID
    property_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
