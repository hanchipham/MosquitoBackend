import secrets
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials, APIKeyQuery
from app.models.device import DeviceAuth, Device
from app.database import get_db
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()
docs_api_key = APIKeyQuery(name="key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def authenticate_device(device_code: str, password: str, db: Session) -> Device:
    """
    Authenticate device using device_code and password
    Returns Device object if authentication successful
    Raises HTTPException if authentication failed
    """
    device_auth = db.query(DeviceAuth).filter(
        DeviceAuth.device_code == device_code
    ).first()
    
    if not device_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not verify_password(password, device_auth.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    device = db.query(Device).filter(Device.id == device_auth.device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is not active"
        )
    
    return device


def get_current_device(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Device:
    """
    Dependency untuk mendapatkan device yang terautentikasi
    Menggunakan HTTP Basic Auth
    """
    return authenticate_device(credentials.username, credentials.password, db)


def verify_docs_api_key(api_key: str = Depends(docs_api_key)):
    """
    Dependency untuk autentikasi akses dokumentasi API
    Menggunakan simple API key via query parameter
    Akses: /docs?key=mosquitoDocs
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Access: /docs?key=YOUR_KEY",
        )
    
    if not secrets.compare_digest(api_key, settings.DOCS_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key
