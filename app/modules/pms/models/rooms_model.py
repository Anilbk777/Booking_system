from decimal import Decimal
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID,JSONB, ARRAY
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

from app.utils.timestamp import TimestampMixin


class RoomStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    BOOKED="BOOKED"
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

  # --- Rooms Model ---
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
            "property_id", "room_name", name="uq_rooms_property_id_room_name"
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

    # ─── HYBRID CANCELLATION POLICY STORAGE ──────────────────────────
    # 1. The Enum tracking the categorical selection (FLEXIBLE, CUSTOM, etc.)
    cancellation_policy: Mapped[CancellationPolicy] = mapped_column(
        SqlEnum(CancellationPolicy, native_enum=False, length=50),
        nullable=False,
        default=CancellationPolicy.FLEXIBLE,
    )
    # 2. Text Snapshot: The literal Title shown to guests (Resolves Default or Custom)
    cancellation_title: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        default="Flexible Cancellation"
    )
    # 3. Text Snapshot: The actual contract rules description text
    cancellation_description: Mapped[str] = mapped_column(
        String(2000), 
        nullable=False, 
        default="Full refund if cancelled up to 24 hours before check-in."
    )
    
    # ─── OPTIMIZED PHOTOS (Embedded JSONB) ───────────────────────────
    # Handles 1 cover photo easily. Format: {"cover": "url", "gallery": ["url1"]}
    photos: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, 
        server_default='{"cover": null, "gallery": []}', 
        nullable=False
    )   

    # ─── OPTIMIZED AMENITIES (No Junction Tables) ────────────────────
    # References row UUIDs from the global master 'amenities' table
    system_amenity_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), 
        server_default="{}", 
        nullable=False
    )
    # Inline custom amenities unique to this exact room tier
    custom_amenities: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB, 
        server_default="[]", 
        nullable=False
    )

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="rooms")
    bed_type: Mapped["BedType"] = relationship("BedType", back_populates="rooms")
    room_type: Mapped["RoomType"] = relationship("RoomType", back_populates="rooms")


# --- RoomType Catalog Model ---
class RoomType(Base, TimestampMixin):
    __tablename__ = "room_types"
    __table_args__ = (
        UniqueConstraint(
            "property_id", "room_type_name", name="uq_room_types_property_id_room_type_name"
        ),
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
    property_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    room_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    property: Mapped["Property"] = relationship("Property", back_populates="room_types")
    rooms: Mapped[List["Rooms"]] = relationship("Rooms", back_populates="room_type")


# --- BedType Catalog Model ---
class BedType(Base, TimestampMixin):
    __tablename__ = "bed_types"
    __table_args__ = (
        UniqueConstraint(
            "property_id", "bed_name", name="uq_bed_types_property_id_bed_name"
        ),
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
    property_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    bed_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    property: Mapped["Property"] = relationship("Property", back_populates="bed_types")
    rooms: Mapped[List["Rooms"]] = relationship("Rooms", back_populates="bed_type")
