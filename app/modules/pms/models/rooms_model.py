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
    ARRAY,
    Enum as SqlEnum,
    Index,
    DateTime,
    func,
)
from app.config.database_config import Base
from typing import Optional, List
from enum import StrEnum
from app.modules.pms.models.properties_model import PropertyHotelDetail
from datetime import datetime


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
# Mixins
# ---------------------------------------------------------------------------


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # Tells PostgreSQL to store TZ info
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# RoomType
# ---------------------------------------------------------------------------


class RoomType(Base, TimestampMixin):
    __tablename__ = "room_types"
    __table_args__ = (
        # prevent duplicate custom type names per property
        UniqueConstraint(
            "hotel_detail_id", "room_name", name="uq_room_types_hotel_detail_id_room_name"
        ),
        Index(
            "ix_room_types_unique_default_name",
            "room_name",
            unique=True,
            postgresql_where="is_default = true",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_detail_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("property_hotel_details.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    room_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    property_Hotel: Mapped["PropertyHotelDetail"] = relationship(
        "PropertyHotelDetail", back_populates="room_types"
    )
    rooms: Mapped[List["Rooms"]] = relationship("Rooms", back_populates="room_type")


# ---------------------------------------------------------------------------
# BedType
# ---------------------------------------------------------------------------


class BedType(Base, TimestampMixin):
    __tablename__ = "bed_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hotel_detail_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("property_hotel_details.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    bed_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # sort_order so defaults appear before customs in dropdowns
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    property_Hotel: Mapped["PropertyHotelDetail"] = relationship(
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

    room: Mapped["Rooms"] = relationship("Rooms", back_populates="room_photos")


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
    photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_photos.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    room_name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_adults: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_children: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    amenities: Mapped[List[str]] = mapped_column(
        ARRAY(String(100)), nullable=False, default=list
    )

    base_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[RoomStatus] = mapped_column(
        SqlEnum(RoomStatus, native_enum=False, length=50),
        default=RoomStatus.AVAILABLE,
        nullable=False,
    )
    cancellation_policy: Mapped[CancellationPolicy] = mapped_column(
        SqlEnum(CancellationPolicy, native_enum=False, length=20),
        nullable=False,
        default=CancellationPolicy.FLEXIBLE,
    )
    cancellation_notes: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )

    # Relationships
    property_Hotel: Mapped["PropertyHotelDetail"] = relationship(
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
