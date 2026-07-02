import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator,ConfigDict,field_serializer


# 1. Shared Enum (Matches your Database Configuration)
class DiscountType(str, Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"


# 2. Base Configuration (Shared across fields)
class DiscountCodeBase(BaseModel):
    code: str = Field(...,title="Code", min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", description="Alphanumeric code in uppercase")
    type: DiscountType = Field(...,title="Discount Type")
    discount_value: float = Field(...,title="Discount Value", gt=0, description="Discount value must be greater than 0")
    min_amount: float = Field(default=0.0,title="Minimum Amount", ge=0, description="Minimum order amount must be 0 or positive")
    max_uses: int = Field(...,title="Maximum Uses", gt=0, description="Max uses must be greater than 0")
    valid_from: datetime 
    valid_to: datetime 

    # Strip whitespace and convert code string to uppercase automatically
    @field_validator("code")
    @classmethod
    def clean_code(cls, v: str) -> str:
        return v.strip().upper()

    # Enforce percentage ceiling validation logic
    @field_validator("discount_value")
    @classmethod
    def validate_percentage(cls, v: float, info) -> float:
        # Check if 'type' is accessible and equals PERCENTAGE
        if "type" in info.data and info.data["type"] == DiscountType.PERCENTAGE:
            if v > 100:
                raise ValueError("Percentage discount cannot exceed 100%")
        return v
    


# 3. Create Schema (Request body for POST requests)
class DiscountCodeCreate(DiscountCodeBase):
    # Cross-field validation to ensure dates make logical sense
    @model_validator(mode="after")
    def validate_date_range(self) -> "DiscountCodeCreate":
        if self.valid_to <= self.valid_from:
            raise ValueError("Valid to date must occur strictly after the valid from date")
        return self


# 4. Update Schema (Request body for PATCH requests - all fields optional)
class DiscountCodeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50, pattern=r"^[A-Z0-9_-]+$")
    type: Optional[DiscountType] = None
    discount_value: Optional[float] = Field(None, gt=0)
    min_amount: Optional[float] = Field(None, ge=0)
    max_uses: Optional[int] = Field(None, gt=0)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

    @field_validator("code")
    @classmethod
    def clean_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().upper()
        return v

    @model_validator(mode="after")
    def validate_update_fields(self) -> "DiscountCodeUpdate":
        # Percentage caps check on update values
        current_type = self.type
        if self.value is not None and current_type == DiscountType.PERCENTAGE and self.value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")

        # Date chronologies check on update parameters
        if self.valid_from is not None and self.valid_to is not None:
            if self.valid_to <= self.valid_from:
                raise ValueError("valid_to date must occur strictly after valid_from date")
        return self


# 5. Response Schema (Returned from API endpoints)
class DiscountCodeResponse(DiscountCodeBase):
    id: uuid.UUID
    property_id: uuid.UUID
    used_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("valid_from", "valid_to", when_used="json")
    def serialize_local_tz(self, dt: datetime) -> str:
        if dt is None:
            return None
        # Returns the exact ISO string including your +05:45 offset
        return dt.isoformat()

