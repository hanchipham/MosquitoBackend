"""
Device Control Service - Simplified Version

Design Philosophy:
- ONE control status per device (not queue-based)
- Simple status tracking: PENDING → EXECUTED/FAILED
- IoT updates status after execution
- Message and timestamp for transparency
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.models.manual_control import DeviceControl, generate_uuid
from app.models.device import Device
from app.config import get_current_time


class DeviceControlService:
    """Service for managing device control (simplified)"""

    @staticmethod
    def get_control(db: Session, device_code: str) -> Optional[DeviceControl]:
        """
        Get current control status for device
        
        Args:
            db: Database session
            device_code: Device identifier
            
        Returns:
            DeviceControl object if exists, None otherwise
        """
        return db.query(DeviceControl).filter(
            DeviceControl.device_code == device_code
        ).first()

    @staticmethod
    def set_control(
        db: Session,
        device_code: str,
        control_command: str,
        message: Optional[str] = None
    ) -> DeviceControl:
        """
        Set control command for device (upsert)
        
        Creates new control if doesn't exist, updates if exists
        
        Args:
            db: Database session
            device_code: Device identifier
            control_command: Command (ACTIVATE, SLEEP, ACTIVATE_SERVO, STOP_SERVO)
            message: Optional message
            
        Returns:
            DeviceControl object
            
        Raises:
            ValueError: If device not found
        """
        # Verify device exists
        device = db.query(Device).filter(Device.device_code == device_code).first()
        if not device:
            raise ValueError(f"Device {device_code} not found")

        # Check if control already exists
        control = DeviceControlService.get_control(db, device_code)
        
        if control:
            # Update existing control
            control.control_command = control_command
            control.status = "PENDING"
            control.message = message or f"Control set to {control_command}"
            control.updated_at = get_current_time()
        else:
            # Create new control
            control = DeviceControl(
                id=generate_uuid(),
                device_id=device.id,
                device_code=device_code,
                control_command=control_command,
                status="PENDING",
                message=message or f"Control initialized to {control_command}",
                created_at=get_current_time(),
                updated_at=get_current_time()
            )
            db.add(control)
        
        db.commit()
        db.refresh(control)
        return control

    @staticmethod
    def update_status(
        db: Session,
        device_code: str,
        status: str,
        message: Optional[str] = None
    ) -> Optional[DeviceControl]:
        """
        Update control status (called by IoT after execution)
        
        Args:
            db: Database session
            device_code: Device identifier
            status: New status (EXECUTED, FAILED)
            message: Optional message from IoT
            
        Returns:
            Updated DeviceControl object, or None if not found
        """
        control = DeviceControlService.get_control(db, device_code)
        
        if not control:
            return None
        
        control.status = status
        control.message = message or f"Status updated to {status}"
        control.updated_at = get_current_time()
        
        db.commit()
        db.refresh(control)
        return control

    @staticmethod
    def get_control_response(
        db: Session,
        device_code: str,
        automatic_action: str
    ) -> Dict[str, Any]:
        """
        Get control response for IoT polling
        
        Priority: Manual control overrides automatic if status=PENDING
        
        Args:
            db: Database session
            device_code: Device identifier
            automatic_action: Action from inference (ACTIVATE/SLEEP)
            
        Returns:
            Control response with mode, command/action, status, message, timestamp
        """
        control = DeviceControlService.get_control(db, device_code)
        
        # If control exists and status is PENDING, return manual control
        if control and control.status == "PENDING":
            return {
                "mode": "MANUAL",
                "command": control.control_command,
                "status": control.status,
                "message": control.message,
                "timestamp": control.updated_at.isoformat()
            }
        else:
            # Return automatic control
            return {
                "mode": "AUTO",
                "action": automatic_action,
                "status": "AUTO",
                "message": "Automatic control based on inference",
                "timestamp": get_current_time().isoformat()
            }

    @staticmethod
    def reset_control(db: Session, device_code: str) -> bool:
        """
        Reset control to default state
        
        Args:
            db: Database session
            device_code: Device identifier
            
        Returns:
            True if deleted, False if not found
        """
        control = DeviceControlService.get_control(db, device_code)
        
        if control:
            db.delete(control)
            db.commit()
            return True
        
        return False
