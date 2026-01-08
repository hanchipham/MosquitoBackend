"""Create test device with credentials"""
import uuid
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
from datetime import datetime

# Database connection
DATABASE_URL = "mysql+pymysql://root:root123@localhost:3306/mosquito_db"
engine = create_engine(DATABASE_URL)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_device():
    """Create test device: device_code='test', password='123'"""
    
    device_id = str(uuid.uuid4())
    device_code = "test"
    password = "123"
    password_hash = pwd_context.hash(password)
    now = datetime.now()
    
    with engine.connect() as conn:
        # Check if device exists
        result = conn.execute(
            text("SELECT id FROM devices WHERE device_code = :code"),
            {"code": device_code}
        )
        existing = result.fetchone()
        
        if existing:
            print(f"✓ Device '{device_code}' already exists")
            device_id = existing[0]
            
            # Update password
            conn.execute(
                text("UPDATE device_auth SET password_hash = :hash WHERE device_code = :code"),
                {"hash": password_hash, "code": device_code}
            )
            conn.commit()
            print(f"✓ Password updated for device '{device_code}'")
        else:
            # Insert device
            conn.execute(
                text("""
                    INSERT INTO devices (id, device_code, location, description, is_active, created_at)
                    VALUES (:id, :code, :loc, :desc, :active, :created)
                """),
                {
                    "id": device_id,
                    "code": device_code,
                    "loc": "Test Location",
                    "desc": "Test device for API testing",
                    "active": True,
                    "created": now
                }
            )
            
            # Insert auth
            auth_id = str(uuid.uuid4())
            conn.execute(
                text("""
                    INSERT INTO device_auth (id, device_id, device_code, password_hash)
                    VALUES (:id, :device_id, :code, :hash)
                """),
                {
                    "id": auth_id,
                    "device_id": device_id,
                    "code": device_code,
                    "hash": password_hash
                }
            )
            
            conn.commit()
            print(f"✓ Created device '{device_code}'")
        
        print(f"\nDevice Credentials:")
        print(f"  Device Code: {device_code}")
        print(f"  Password: {password}")
        print(f"  Device ID: {device_id}")

if __name__ == "__main__":
    print("Creating test device...\n")
    create_test_device()
    print("\n✅ Done! You can now test with these credentials:")
    print("   Device Code: test")
    print("   Password: 123")
