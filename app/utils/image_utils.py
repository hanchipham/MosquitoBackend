import os
import hashlib
from datetime import datetime
from PIL import Image
from typing import Tuple
from app.config import get_current_time


def ensure_directory_exists(path: str):
    """Pastikan directory exists, buat jika belum ada"""
    os.makedirs(path, exist_ok=True)


def save_image(image_data: bytes, file_path: str) -> Tuple[int, int, str]:
    """
    Save image to filesystem
    Returns: (width, height, checksum)
    """
    # Ensure directory exists
    directory = os.path.dirname(file_path)
    ensure_directory_exists(directory)
    
    # Save image
    with open(file_path, 'wb') as f:
        f.write(image_data)
    
    # Get image dimensions
    with Image.open(file_path) as img:
        width, height = img.size
    
    # Calculate checksum
    checksum = hashlib.sha256(image_data).hexdigest()
    
    return width, height, checksum


def preprocess_image(input_path: str, output_path: str) -> Tuple[int, int, str, bytes]:
    """
    Preprocess image (resize, enhance, etc.)
    Returns: (width, height, checksum, image_data)
    """
    # Ensure output directory exists
    directory = os.path.dirname(output_path)
    ensure_directory_exists(directory)
    
    # Open and process image
    with Image.open(input_path) as img:
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large (max 1024x1024)
        max_size = 1024
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save preprocessed image
        img.save(output_path, 'JPEG', quality=90)
        
        width, height = img.size
    
    # Read image data for blob storage
    with open(output_path, 'rb') as f:
        image_data = f.read()
    
    # Calculate checksum
    checksum = hashlib.sha256(image_data).hexdigest()
    
    return width, height, checksum, image_data


def generate_image_filename(device_code: str, image_type: str = "original") -> str:
    """Generate unique filename for image"""
    timestamp = get_current_time().strftime("%Y%m%d_%H%M%S_%f")
    return f"{device_code}_{image_type}_{timestamp}.jpg"
