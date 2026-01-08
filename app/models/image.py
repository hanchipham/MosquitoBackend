import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, LargeBinary
from sqlalchemy.dialects.mysql import CHAR, LONGBLOB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base
from app.config import get_current_time


def generate_uuid():
    return str(uuid.uuid4())


class Image(Base):
    __tablename__ = "images"
    
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=generate_uuid)
    device_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("devices.id"), nullable=False)
    device_code: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    image_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # original | preprocessed
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_blob: Mapped[Optional[bytes]] = mapped_column(LONGBLOB, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    
    # Relationships
    device = relationship("Device", back_populates="images")
    inference_result = relationship("InferenceResult", back_populates="image", uselist=False)
