from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
from typing import Optional
import uuid

from app.database import Base
from app.config import get_current_time


def generate_uuid():
    """Generate UUID as string for MySQL CHAR(36) compatibility"""
    return str(uuid.uuid4())


class DeviceControl(Base):
    """
    Device Control Model - Simple control status per device
    
    Design Philosophy:
    - ONE control status per device (simple, not queue-based)
    - Admin/API sets control command
    - IoT executes and updates status
    - Track message and timestamp for transparency
    
    Workflow:
    1. Admin sets command → status=PENDING
    2. IoT polls → gets command
    3. IoT executes → updates status to EXECUTED
    4. Track message and timestamp throughout
    """
    __tablename__ = "device_controls"

    # Primary Key
    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=generate_uuid
    )

    # Foreign Keys
    device_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # ONE control per device
        index=True
    )

    # Device Reference (denormalized)
    device_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,  # ONE control per device_code
        index=True
    )

    # Control Command
    control_command: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ACTIVATE | SLEEP | ACTIVATE_SERVO | STOP_SERVO"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
        comment="PENDING | EXECUTED | FAILED"
    )

    # Message (from IoT or admin)
    message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=get_current_time,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=get_current_time,
        onupdate=get_current_time,
        nullable=False
    )

    # Relationships
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="control"
    )

    def __repr__(self):
        return (
            f"<DeviceControl(device_code={self.device_code}, "
            f"command={self.control_command}, status={self.status})>"
        )
