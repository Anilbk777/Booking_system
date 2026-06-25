from pydantic import BaseModel, Field, ConfigDict, field_validator, validator
from typing import Optional
import uuid
from zoneinfo import ZoneInfo
from datetime import datetime


class TenantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, strip_whitespace=True)
    slug: Optional[str] = Field(
        default=None, min_length=2, max_length=100, strip_whitespace=True
    )
    custom_domain: Optional[str] = Field(default=None)
    logo_url: Optional[str] = Field(default=None)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="UTC", min_length=3, max_length=100)

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


class TenantCreateSchema(TenantBase):
    @validator("slug", always=True)
    def generate_slug(cls, v, values):
        if v:
            return v
        name = values.get("name")
        if name:
            return name.lower().replace(" ", "-")
        return None


class TenantResponseSchema(TenantBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TenantUpdateSchema(BaseModel):
    name: Optional[str] = Field(
        None, min_length=2, max_length=255, strip_whitespace=True
    )
    slug: Optional[str] = Field(
        None, min_length=2, max_length=100, strip_whitespace=True
    )
    custom_domain: Optional[str] = None
    logo_url: Optional[str] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    timezone: Optional[str] = Field(None, min_length=3, max_length=100)
