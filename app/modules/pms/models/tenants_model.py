import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, ForeignKey, UniqueConstraint, Enum as SqlEnum
from app.config.database_config import Base

from typing import Optional, List
from enum import StrEnum


class Plan(StrEnum):
    FREE = "Free"
    PREMIUM = "Premium"
    ENTERPRISE = "Enterprise"


class Status(StrEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
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
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tenant_owner_name"),
    )
    # --- Relationships ---
    # 1. The specific Admin who created/owns this workspace
    owner: Mapped["User"] = relationship(
        "User", foreign_keys=[owner_id], back_populates="owned_tenants"
    )
    
    # 2. All the users (Admins, Managers, Receptionists) who work in this workspace
    staff_members: Mapped[List["User"]] = relationship(
        "User", foreign_keys="[User.tenant_id]", back_populates="workspace", cascade="all, delete-orphan"
    )
    
    properties: Mapped[List["Property"]] = relationship(
        "Property", back_populates="tenant", cascade="all, delete-orphan"
    )
    loyalty_profiles: Mapped[List["GuestLoyalty"]] = relationship(
        "GuestLoyalty", back_populates="tenant", cascade="all, delete-orphan"
    )
