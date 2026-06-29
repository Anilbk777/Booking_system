import uuid
from datetime import datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database_config import Base
from app.modules.pms.models.tenants_model import Tenant


class PropertyType(StrEnum):
    HOTEL = "HOTEL"
    HOSTEL = "HOSTEL"
    VILLA = "VILLA"
    APARTMENT = "APARTMENT"
    RESORT = "RESORT"
    GUESTHOUSE = "GUESTHOUSE"
    RESTURANT = "RESTURANT"
    OTHER = "OTHER"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------


class Property(Base, TimestampMixin):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_property_name"),
        Index("ix_properties_geo_location", "country", "state", "city"),
    )

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
        SqlEnum(PropertyType, native_enum=False, length=20),
        nullable=False,
        default=PropertyType.HOTEL,
    )
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    country: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=9, scale=6), nullable=True
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=9, scale=6), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="properties")
    hotel_detail: Mapped["PropertyHotelDetail"] = relationship(
        "PropertyHotelDetail",
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    photos: Mapped[List["PropertyPhoto"]] = relationship(
        "PropertyPhoto",
        back_populates="property",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # 1. Direct one-to-many relationship: Custom amenities *owned* by this specific property
    owned_custom_amenities: Mapped[List["Amenity"]] = relationship(
        "Amenity",
        back_populates="owning_property",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 2. Direct junction relationship: Which records are selected for this property
    property_amenities: Mapped[List["PropertyAmenity"]] = relationship(
        "PropertyAmenity",
        back_populates="property",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    special_offers: Mapped[List["SpecialOffer"]] = relationship(
        "SpecialOffer",
        back_populates="property",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ---------------------------------------------------------------------------
# PropertyHotelDetail
# ---------------------------------------------------------------------------


class PropertyHotelDetail(Base, TimestampMixin):
    __tablename__ = "property_hotel_details"
    __table_args__ = (
        CheckConstraint(
            "check_in_time_to > check_in_time_from",
            name="chk_check_in_time_order",
        ),
        CheckConstraint(
            "check_out_time_to > check_out_time_from",
            name="chk_check_out_time_order",
        ),
        CheckConstraint(
            "number_of_floors >= 1",
            name="chk_min_floors",
        ),
        CheckConstraint(
            "total_rooms >= 0",
            name="chk_total_rooms_non_negative",
        ),
        CheckConstraint(
            "year_built >= 1800 AND year_built <= 2100",
            name="chk_year_built_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        index=True,
        unique=True,
        nullable=False,
    )
    check_in_time_from: Mapped[time] = mapped_column(
        Time, default=time(9, 0), nullable=False
    )
    check_in_time_to: Mapped[time] = mapped_column(
        Time, default=time(12, 0), nullable=False
    )
    check_out_time_from: Mapped[time] = mapped_column(
        Time, default=time(12, 0), nullable=False
    )
    check_out_time_to: Mapped[time] = mapped_column(
        Time, default=time(13, 0), nullable=False
    )
    number_of_floors: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_rooms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    property: Mapped["Property"] = relationship(
        "Property", back_populates="hotel_detail"
    )
    room_types: Mapped[List["RoomType"]] = relationship(
        "RoomType", back_populates="hotel_detail", cascade="all, delete-orphan"
    )
    bed_types: Mapped[List["BedType"]] = relationship(
        "BedType", back_populates="hotel_detail", cascade="all, delete-orphan"
    )
    rooms: Mapped[List["Rooms"]] = relationship(
        "Rooms", back_populates="hotel_detail", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# PropertyPhoto
# ---------------------------------------------------------------------------


class PropertyPhoto(Base, TimestampMixin):
    __tablename__ = "property_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    photo_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="photos")


# ---------------------------------------------------------------------------
# Amenity  — global defaults (property_id IS NULL) + per-property custom amenities
# ---------------------------------------------------------------------------


class Amenity(Base, TimestampMixin):
    __tablename__ = "amenities"
    __table_args__ = (
        # A property cannot have two custom amenities with the same name
        UniqueConstraint(
            "property_id",
            "name",
            name="uq_amenities_property_id_name",
        ),
        # Among global defaults, name must be globally unique
        Index(
            "ix_amenities_unique_default_name",
            "name",
            unique=True,
            sqlite_where=text("is_default = 1"),
            postgresql_where=text("is_default = true"),
        ),
        # A global default amenity must NOT belong to a specific property
        CheckConstraint(
            "NOT (is_default = true AND property_id IS NOT NULL)",
            name="chk_default_amenity_no_property",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # NULL  → global default, visible to every property
    # <id>  → custom amenity belonging to this property only
    property_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=True,  # NULL = global default
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Back-populates the direct ownership line
    owning_property: Mapped[Optional["Property"]] = relationship(
        "Property", back_populates="owned_custom_amenities"
    )

    # Back-populates tracking selections inside the intermediate junction mapping
    property_amenities: Mapped[List["PropertyAmenity"]] = relationship(
        "PropertyAmenity",
        back_populates="amenity",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ---------------------------------------------------------------------------
# PropertyAmenity  — which amenities a property has selected
# ---------------------------------------------------------------------------


class PropertyAmenity(Base, TimestampMixin):
    __tablename__ = "property_amenities"
    __table_args__ = (
        UniqueConstraint(
            "property_id",
            "amenity_id",
            name="uq_property_amenities_property_amenity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    amenity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("amenities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Relationships
    # Clean direct back-references to both tables
    property: Mapped["Property"] = relationship(
        "Property", back_populates="property_amenities"
    )
    amenity: Mapped["Amenity"] = relationship(
        "Amenity", back_populates="property_amenities"
    )
