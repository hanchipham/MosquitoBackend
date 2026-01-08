from pydantic_settings import BaseSettings
from typing import Optional
from datetime import datetime, timezone, timedelta
import zoneinfo


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/mosquito_db"
    
    # Roboflow
    ROBOFLOW_API_KEY: str = ""
    ROBOFLOW_WORKSPACE: Optional[str] = None
    ROBOFLOW_WORKFLOW_ID: Optional[str] = None
    # Legacy support for model-based detection
    ROBOFLOW_MODEL_ID: Optional[str] = None
    ROBOFLOW_VERSION: Optional[int] = None
    
    # Blynk
    BLYNK_AUTH_TOKEN: Optional[str] = None
    BLYNK_TEMPLATE_ID: Optional[str] = None
    BLYNK_DEVICE_NAME: str = "mosquito_detector"
    
    # Storage
    STORAGE_PATH: str = "./storage"
    IMAGE_ORIGINAL_PATH: str = "./storage/images/original"
    IMAGE_PREPROCESSED_PATH: str = "./storage/images/preprocessed"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Timezone (e.g., 'Asia/Jakarta' for WIB, 'UTC', 'America/New_York')
    TIMEZONE: str = "UTC"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_current_time() -> datetime:
    """Get current datetime with configured timezone"""
    try:
        tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
    except Exception:
        # Fallback to UTC if timezone not found
        tz = timezone.utc
    return datetime.now(tz)
