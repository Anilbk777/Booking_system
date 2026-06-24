import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    Integer,
    Boolean,
    Date,
    UniqueConstraint,
    CheckConstraint,
    ARRAY,
    Enum as SqlEnum,
)
from app.config.database_config import Base
from typing import Optional, List
from enum import StrEnum
from app.modules.pms.models.properties_model import Property
from datetime import date


class RoomType(Base):
    __tablename__ = "room_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    room_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # relationships
    property: Mapped["Property"] = relationship("Property", back_populates="room_types")


class Bed_Type(Base):
    __tablename__ = "bed_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_types.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    bed_name: Mapped[str] = mapped_column(String(100), nullable=False)


class Rooms(Base):
    __tablename__ = "rooms"

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
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    room_name: Mapped[str] = mapped_column(String(100), nullable=False)

    max_adults: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint(
            "max_adults >= 1 AND max_adults <= 30", name="chk_max_adults_range"
        ),
        default=2,
        nullable=False,
    )
    max_children: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint(
            "max_children >= 0 AND max_children <= 15", name="chk_max_children_range"
        ),
        default=0,
        nullable=False,
    )
    amenaties: Mapped[List[str]] = mapped_column(ARRAY(String(255)), nullable=False)

    base_rate: Mapped[float] = mapped_column(
        Numeric(10, 2),
        CheckConstraint("base_rate >= 0 ", name="chk_base_rate_positive"),
        nullable=True,
    )
    cancellation_policy: Mapped[str] = mapped_column(String(1000), nullable=True)
    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="rooms")
    room_photos: Mapped[List["RoomPhoto"]] = relationship(
        "RoomPhoto", back_populates="room", cascade="all, delete-orphan"
    )


class RoomPhoto(Base):
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
    photo_url: Mapped[str] = mapped_column(String(2048), nullable=True)

    room: Mapped["Room"] = relationship("Room", back_populates="room_photos")


# class PropertyRoomUnit(Base):
#     __tablename__ = "room_units"

#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
#     )
#     property_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("properties.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     room_type_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("room_types.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     room_number: Mapped[str] = mapped_column(String(20), nullable=False)
#     floor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
#     status: Mapped[RoomStatus] = mapped_column(
#         SqlEnum(RoomStatus, native_enum=False, length=50), default=RoomStatus.AVAILABLE, nullable=False
#     )
#     smoking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
#     accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

#     # Enforce unique room numbers per property location
#     __table_args__ = (
#         UniqueConstraint("property_id", "room_number", name="uq_property_room_number"),
#     )

#     # Relationships
#     property: Mapped["Property"] = relationship("Property", back_populates="room_units")
#     room_type: Mapped["RoomType"] = relationship(
#         "RoomType", back_populates="room_units"
#     )


# class RatePlan(Base):
#     __tablename__ = "rate_plans"

#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
#     )
#     property_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("properties.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     room_type_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("room_types.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     name: Mapped[str] = mapped_column(
#         String(100), nullable=False
#     )  # Non-Refundable, Room Only, etc.
#     includes_breakfast: Mapped[bool] = mapped_column(
#         Boolean, default=False, nullable=False
#     )
#     includes_dinner: Mapped[bool] = mapped_column(
#         Boolean, default=False, nullable=False
#     )
#     includes_lunch: Mapped[bool] = mapped_column(
#         Boolean, default=False, nullable=False
#     )

#     price_per_night: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
#     min_stay_nights: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
#     cancellation_policy: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

#     # Relationships
#     property: Mapped["Property"] = relationship("Property", back_populates="rate_plans")
#     room_type: Mapped["RoomType"] = relationship(
#         "RoomType", back_populates="rate_plans"
#     )


# class DateOverride(Base):
#     __tablename__ = "date_overrides"

#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
#     )
#     property_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("properties.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     room_type_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("room_types.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     rate_plan_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("rate_plans.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     start_date: Mapped[date] = mapped_column(Date, nullable=False)
#     end_date: Mapped[date] = mapped_column(Date, nullable=False)
#     override_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
#     is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# class DiscountCode(Base):
#     __tablename__ = "discount_codes"

#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
#     )
#     property_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey("properties.id", ondelete="CASCADE"),
#         index=True,
#         nullable=False,
#     )
#     code: Mapped[str] = mapped_column(String(50), nullable=False)
#     type: Mapped[str] = mapped_column(
#         String(20), default="percentage", nullable=False
#     )  # fixed, percentage
#     value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
#     min_amount: Mapped[float] = mapped_column(
#         Numeric(10, 2), default=0.00, nullable=False
#     )
#     max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
#     valid_from: Mapped[date] = mapped_column(Date, nullable=False)
#     valid_to: Mapped[date] = mapped_column(Date, nullable=False)

#     __table_args__ = (
#         UniqueConstraint("property_id", "code", name="uq_property_discount_code"),
#     )
