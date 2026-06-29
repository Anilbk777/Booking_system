import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class SpecialOfferBase(BaseModel):
    title: str = Field(
        ...,
        title="Offer Title",
        description="Title name of the special offer deal",
        min_length=2,
        max_length=100,
        examples=["Early Bird 15%"],
    )
    description: Optional[str] = Field(None, max_length=1000, title="Offer Description", description="Description of the special offer deal")
    discount_percentage: float = Field(
        float("0.00"),
        ge=0.00,
        le=100.00,
        title="Discount Percentage",
        description="Discount percentage of the special offer deal",
        examples=[15.00],
    )
    start_date: date = Field(..., title="Start Date", description="Active starting date window")
    end_date: date = Field(..., title="End Date", description="Active termination date window")
    is_active: bool = Field(default=False, title="Is Active", description="Is the special offer active")
    is_custom: bool = Field(default=False, title="Is Custom", description="Is the special offer custom")

    @model_validator(mode="after")
    def validate_offer_chronology(self) -> "SpecialOfferBase":
        """Validate date windows and prevent retroactive past schedules."""
        if self.start_date >= self.end_date:
            raise ValueError(
                "The offer start_date must be strictly earlier than the end_date."
            )

        if self.start_date < date.today():
            raise ValueError("The offer start_date cannot be set in the past.")

        return self


# Bulk payload wrapper mapping array list
class SpecialOffersCreate(BaseModel):
    offers: List[SpecialOfferBase] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_unique_titles(self) -> "SpecialOffersCreate":
        """Prevent submitting multiple offers with identical titles in the same payload."""
        seen_titles = set()
        for offer in self.offers:
            normalized_title = offer.title.strip().lower()
            if normalized_title in seen_titles:
                raise ValueError(
                    f"Duplicate offer title found in request: '{offer.title}'. Titles must be unique."
                )
            seen_titles.add(normalized_title)
        return self





class SpecialOfferResponse(TimestampSchema):
    id: uuid.UUID
    property_id: uuid.UUID
    title: str
    description: Optional[str]
    discount_percentage: float 
    start_date: date
    end_date: date
    is_active: bool
    is_custom: bool
    model_config = ConfigDict(from_attributes=True)