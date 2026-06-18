from pydantic import BaseModel, Field, ConfigDict, field_validator
import uuid
from typing import Optional
from datetime import time, datetime
from app.modules.pms.models.properties_model import PropertyType


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


class PropertyResponse(PropertyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
