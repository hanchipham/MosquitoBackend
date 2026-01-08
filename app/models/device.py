import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.config import get_current_time


def generate_uuid():
    return str(uuid.uuid4())


class Device(Base):
    __tablename__ = "devices"
    
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=generate_uuid)
    device_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    
    # Relationships
    auth = relationship("DeviceAuth", back_populates="device", uselist=False)
    images = relationship("Image", back_populates="device")
    inference_results = relationship("InferenceResult", back_populates="device")
    alerts = relationship("Alert", back_populates="device")
    control = relationship("DeviceControl", back_populates="device", uselist=False)


class DeviceAuth(Base):
    __tablename__ = "device_auth"
    
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=generate_uuid)
    device_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("devices.id"), nullable=False)
    device_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="auth")
