from pydantic import BaseModel, Field, ConfigDict, field_validator, validator
from typing import Optional
import uuid
from zoneinfo import ZoneInfo
from datetime import datetime


class TenantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, strip_whitespace=True, title="Tenant Name", description="Name of the tenant")
    slug: Optional[str] = Field(
        default=None, min_length=2, max_length=100, strip_whitespace=True, title="Tenant Slug", description="Slug of the tenant"
    )
    custom_domain: Optional[str] = Field(default=None, title="Custom Domain", description="Custom domain for the tenant")
    logo_url: Optional[str] = Field(default=None, title="Logo URL", description="Logo URL of the tenant")
    currency: str = Field(default="USD", min_length=3, max_length=3, title="Currency", description="Currency of the tenant")
    timezone: str = Field(default="UTC", min_length=3, max_length=100, title="Timezone", description="Timezone of the tenant")

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
        None, min_length=2, max_length=255, strip_whitespace=True,title="Tenant Name", description="Name of the tenant"
    )
    slug: Optional[str] = Field(
        None, min_length=2, max_length=100, strip_whitespace=True,title="Tenant Slug", description="Slug of the tenant"
    )
    custom_domain: Optional[str] = Field(default=None, title="Custom Domain", description="Custom domain for the tenant")
    logo_url: Optional[str] = Field(default=None, title="Logo URL", description="Logo URL of the tenant")
    currency: Optional[str] = Field(None, min_length=3, max_length=3,title="Currency", description="Currency of the tenant")
    timezone: Optional[str] = Field(None, min_length=3, max_length=100,title="Timezone", description="Timezone of the tenant")
