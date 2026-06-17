import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, ForeignKey
from app.config.database_config import Base

from typing import Optional, List

from app.modules.auth.models.users_model import User

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="Trial", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active", nullable=False)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)

    owner: Mapped["User"] = relationship("User", back_populates="owned_tenants")
    loyalty_profiles: Mapped[List["GuestLoyalty"]] = relationship(
        "GuestLoyalty", 
        back_populates="tenant", 
        cascade="all, delete-orphan"
    )