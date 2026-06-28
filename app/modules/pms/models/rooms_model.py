from decimal import Decimal
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    Integer,
    Boolean,
    UniqueConstraint,
    CheckConstraint,
    Enum as SqlEnum,
    Index,
    text,
)
from app.config.database_config import Base
from typing import Optional, List
from enum import StrEnum
from app.modules.pms.models.properties_model import PropertyHotelDetail, TimestampMixin


class RoomStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    DIRTY = "DIRTY"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class CancellationPolicy(StrEnum):
    FLEXIBLE = "FLEXIBLE"
    MODERATE = "MODERATE"
    STRICT = "STRICT"
    NON_REFUNDABLE = "NON_REFUNDABLE"
    CUSTOM = "CUSTOM"


# ---------------------------------------------------------------------------
# RoomType
# ---------------------------------------------------------------------------


class RoomType(Base, TimestampMixin):
    __tablename__ = "room_types"
    __table_args__ = (
        # Prevent duplicate custom type names per hotel
        UniqueConstraint(
            "hotel_detail_id", "room_type_name", name="uq_room_types_hotel_detail_id_room_type_name"
        ),
        # Among global defaults, room_type_name must be unique
        Index(
            "ix_room_types_unique_default_name",
            "room_type_name",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # NULL → global default available to all hotels; <id> → custom for that hotel only
    hotel_detail_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("property_hotel_details.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    room_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    hotel_detail: Mapped["PropertyHotelDetail"] = relationship(
        "PropertyHotelDetail", back_populates="room_types"
    )
    rooms: Mapped[List["Rooms"]] = relationship("Rooms", back_populates="room_type")


# ---------------------------------------------------------------------------
# BedType
# ---------------------------------------------------------------------------


class BedType(Base, TimestampMixin):
    __tablename__ = "bed_types"
    __table_args__ = (
        # Prevent duplicate custom bed names per hotel
        UniqueConstraint(
            "hotel_detail_id", "bed_name", name="uq_bed_types_hotel_detail_bed_name"
        ),
        # Among global defaults, bed_name must be unique
        Index(
            "ix_bed_types_unique_default_name",
            "bed_name",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # NULL → global default; <id> → custom for that hotel only
    hotel_detail_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("property_hotel_details.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    bed_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    hotel_detail: Mapped["PropertyHotelDetail"] = relationship(
        "PropertyHotelDetail", back_populates="bed_types"
    )
    rooms: Mapped[List["Rooms"]] = relationship("Rooms", back_populates="bed_type")


# ---------------------------------------------------------------------------
# RoomPhoto
# ---------------------------------------------------------------------------


class RoomPhoto(Base, TimestampMixin):
    __tablename__ = "room_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    photo_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_cover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    room: Mapped["Rooms"] = relationship("Rooms", back_populates="room_photos")


# ---------------------------------------------------------------------------
# RoomAmenity — proper join table replacing the ARRAY(String) field
# ---------------------------------------------------------------------------


class RoomAmenity(Base, TimestampMixin):
    __tablename__ = "room_amenities"
    __table_args__ = (
        UniqueConstraint(
            "room_id", "amenity_id", name="uq_room_amenities_room_amenity"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # References the shared Amenity catalogue (global defaults + property customs)
    amenity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("amenities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Relationships
    room: Mapped["Rooms"] = relationship("Rooms", back_populates="room_amenities")
    amenity: Mapped["Amenity"] = relationship("Amenity")

# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------


class Rooms(Base, TimestampMixin):
    __tablename__ = "rooms"
    __table_args__ = (
        CheckConstraint(
            "max_adults >= 1 AND max_adults <= 30", name="chk_max_adults_range"
        ),
        CheckConstraint(
            "max_children >= 0 AND max_children <= 15", name="chk_max_children_range"
        ),
        CheckConstraint("base_rate >= 0", name="chk_base_rate_positive"),
        CheckConstraint("floor_number >= 0", name="chk_floor_number_non_negative"),
        UniqueConstraint(
            "hotel_detail_id", "room_name", name="uq_rooms_hotel_detail_room_name"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_detail_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("property_hotel_details.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    room_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_types.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    bed_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bed_types.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # 0 = ground floor; constraint allows >= 0
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    room_name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_adults: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_children: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    base_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[RoomStatus] = mapped_column(
        SqlEnum(RoomStatus, native_enum=False, length=50),
        default=RoomStatus.AVAILABLE,
        nullable=False,
    )
    cancellation_policy: Mapped[CancellationPolicy] = mapped_column(
        # length=50 — gives room for future longer values like PARTIALLY_REFUNDABLE
        SqlEnum(CancellationPolicy, native_enum=False, length=50),
        nullable=False,
        default=CancellationPolicy.FLEXIBLE,
    )
    cancellation_notes: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )

    # Relationships
    hotel_detail: Mapped["PropertyHotelDetail"] = relationship(
        "PropertyHotelDetail", back_populates="rooms"
    )
    room_photos: Mapped[List["RoomPhoto"]] = relationship(
        "RoomPhoto",
        back_populates="room",
        cascade="all, delete-orphan",
        foreign_keys="RoomPhoto.room_id",
    )
    bed_type: Mapped["BedType"] = relationship("BedType", back_populates="rooms")
    room_type: Mapped["RoomType"] = relationship("RoomType", back_populates="rooms")
    room_amenities: Mapped[List["RoomAmenity"]] = relationship(
        "RoomAmenity", back_populates="room", cascade="all, delete-orphan"
    )
