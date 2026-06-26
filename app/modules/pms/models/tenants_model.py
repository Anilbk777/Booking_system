import uuid
from datetime import datetime
from enum import StrEnum
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database_config import Base


class Plan(StrEnum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"
    ENTERPRISE = "ENTERPRISE"


class Status(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tenant_owner_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE", use_alter=True),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[Plan] = mapped_column(SqlEnum(Plan), default=Plan.FREE, nullable=False)
    status: Mapped[Status] = mapped_column(
        SqlEnum(Status), default=Status.ACTIVE, nullable=False
    )
    custom_domain: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(
        String(3), default="USD", nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)
    # Both timestamps use server_default so DB clock is the single source of truth
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    # 1. The specific Admin who created/owns this workspace
    owner: Mapped["User"] = relationship(
        "User", foreign_keys=[owner_id], back_populates="owned_tenants"
    )

    # 2. All the users (Admins, Managers, Receptionists) who work in this workspace
    staff_members: Mapped[List["User"]] = relationship(
        "User",
        foreign_keys="[User.tenant_id]",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    properties: Mapped[List["Property"]] = relationship(
        "Property", back_populates="tenant", cascade="all, delete-orphan"
    )
    loyalty_profiles: Mapped[List["GuestLoyalty"]] = relationship(
        "GuestLoyalty", back_populates="tenant", cascade="all, delete-orphan"
    )
