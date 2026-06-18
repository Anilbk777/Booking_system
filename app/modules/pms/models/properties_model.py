import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    Integer,
    Time,
    ARRAY,
    Enum as SqlEnum,
    DateTime,
)
from app.config.database_config import Base
from typing import Optional, List
from datetime import time, datetime, UTC
from enum import StrEnum

from app.modules.pms.models.tenants_model import Tenant


class PropertyType(StrEnum):
    HOTEL = "Hotel"
    RESORT = "Resort"
    RESTAURANT = "Restaurant"


class AmenityType(StrEnum):
    POOL = "Pool"
    GYM = "Gym"
    PARKING = "Parking"
    WIFI = "Wifi"
    RESTAURANT = "Restaurant"
    BAR = "Bar"
    SPA = "Spa"
    PET_ALLOWED = "Pet Allowed"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[PropertyType] = mapped_column(
        SqlEnum(PropertyType, native_enum=False, length=50), nullable=False, default=PropertyType.HOTEL
    )
    country: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    lat: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    star_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    check_in_time: Mapped[time] = mapped_column(
        Time, default=time(14, 0), nullable=False
    )
    check_out_time: Mapped[time] = mapped_column(
        Time, default=time(12, 0), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="properties")
    amenities: Mapped[Optional["PropertyAmenity"]] = relationship(
        "PropertyAmenity",
        back_populates="property",
        cascade="all, delete-orphan",
        uselist=False,
    )
    room_types: Mapped[List["RoomType"]] = relationship(
        "RoomType", back_populates="property", cascade="all, delete-orphan"
    )
    room_units: Mapped[List["RoomUnit"]] = relationship(
        "PropertyRoomUnit", back_populates="property", cascade="all, delete-orphan"
    )
    rate_plans: Mapped[List["RatePlan"]] = relationship(
        "RatePlan", back_populates="property", cascade="all, delete-orphan"
    )


class PropertyAmenity(Base):
    __tablename__ = "property_amenities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    amenity: Mapped[List[AmenityType]] = mapped_column(
        ARRAY(SqlEnum(AmenityType, native_enum=False, length=100)), nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="amenities")
