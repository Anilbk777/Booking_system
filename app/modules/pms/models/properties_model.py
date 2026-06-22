import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    Integer,
    ARRAY,
    DateTime,
    Boolean,
    Time,
)
from app.config.database_config import Base
from typing import Optional, List
from datetime import datetime, UTC, time
from decimal import Decimal

from app.modules.pms.models.tenants_model import Tenant


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
    type: Mapped[str] = mapped_column(String(255), nullable=False, default="Hotel")
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    country: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(precision=9, scale=6), nullable=True
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(precision=9, scale=6), nullable=True
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
    year_built: Mapped[int] = mapped_column(Integer, nullable=True)
    amenities: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(255)), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="properties")
    photos: Mapped[List["PropertyPhoto"]] = relationship(
        "PropertyPhoto",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="selectin",  # Automatically fetches photos efficiently using an IN clause when queried
    )


class PropertyPhoto(Base):
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
    photo_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    property: Mapped["Property"] = relationship(
        "Property", back_populates="photos"
    )
