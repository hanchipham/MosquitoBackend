import os
import hashlib
from datetime import datetime
from PIL import Image
from typing import Tuple, Optional
import numpy as np
import cv2
from app.config import get_current_time


def ensure_directory_exists(path: str):
    """Pastikan directory exists, buat jika belum ada"""
    os.makedirs(path, exist_ok=True)


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    Sangat penting untuk ESP32-CAM dengan pencahayaan tidak merata
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(image)


def apply_noise_reduction(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """
    Apply noise reduction menggunakan Non-Local Means Denoising
    Menghilangkan grain sensor dari ESP32-CAM
    """
    return cv2.fastNlMeansDenoising(image, None, h=strength, templateWindowSize=7, searchWindowSize=21)


def apply_sharpening(image: np.ndarray, method: str = "unsharp") -> np.ndarray:
    """
    Apply sharpening untuk menegaskan tepi jentik
    Methods: 'laplacian' atau 'unsharp'
    """
    if method == "laplacian":
        # Laplacian sharpening
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        sharpened = image - 0.7 * laplacian
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    else:
        # Unsharp masking (default) - lebih halus dan natural
        gaussian = cv2.GaussianBlur(image, (0, 0), 3)
        sharpened = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
    
    return sharpened


def apply_morphological_enhancement(
    image: np.ndarray, 
    operation: str = "dilate",
    kernel_size: Tuple[int, int] = (3, 3),
    iterations: int = 1
) -> np.ndarray:
    """
    Apply morphological operations untuk menebalkan jentik yang tipis
    Operations: 'dilate', 'erode', 'open', 'close'
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
    
    if operation == "dilate":
        return cv2.dilate(image, kernel, iterations=iterations)
    elif operation == "erode":
        return cv2.erode(image, kernel, iterations=iterations)
    elif operation == "open":
        return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=iterations)
    elif operation == "close":
        return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=iterations)
    else:
        return image


def enhance_larvae_visibility(
    image: np.ndarray,
    apply_denoise: bool = True,
    apply_clahe_enhancement: bool = True,
    apply_sharp: bool = True,
    apply_morphology: bool = False,
    denoise_strength: int = 10,
    clahe_clip_limit: float = 2.5,
    sharpening_method: str = "unsharp",
    morph_operation: str = "dilate",
    morph_iterations: int = 1
) -> np.ndarray:
    """
    Pipeline lengkap untuk menonjolkan objek linear (jentik) dan menekan latar belakang
    
    Args:
        image: Input image (BGR or Grayscale)
        apply_denoise: Aktifkan noise reduction
        apply_clahe_enhancement: Aktifkan CLAHE untuk kontras adaptif
        apply_sharp: Aktifkan sharpening
        apply_morphology: Aktifkan morphological operations (opsional)
        denoise_strength: Kekuatan noise reduction (default: 10)
        clahe_clip_limit: Clip limit untuk CLAHE (default: 2.5)
        sharpening_method: 'laplacian' atau 'unsharp'
        morph_operation: 'dilate', 'erode', 'open', 'close'
        morph_iterations: Jumlah iterasi morphological operation
    
    Returns:
        Enhanced grayscale image
    """
    # Convert to grayscale jika belum
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Step 1: Noise Reduction
    if apply_denoise:
        gray = apply_noise_reduction(gray, strength=denoise_strength)
    
    # Step 2: CLAHE untuk kontras adaptif lokal
    if apply_clahe_enhancement:
        gray = apply_clahe(gray, clip_limit=clahe_clip_limit)
    
    # Step 3: Sharpening untuk menegaskan tepi jentik
    if apply_sharp:
        gray = apply_sharpening(gray, method=sharpening_method)
    
    # Step 4: Morphological operations (optional)
    if apply_morphology:
        gray = apply_morphological_enhancement(
            gray, 
            operation=morph_operation, 
            iterations=morph_iterations
        )
    
    return gray


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


def preprocess_image(
    input_path: str, 
    output_path: str,
    enhance_for_larvae: bool = True,
    apply_denoise: bool = True,
    apply_clahe_enhancement: bool = True,
    apply_sharp: bool = True,
    apply_morphology: bool = False,
    denoise_strength: int = 10,
    clahe_clip_limit: float = 2.5,
    sharpening_method: str = "unsharp",
    morph_operation: str = "dilate",
    morph_iterations: int = 1,
    save_as_grayscale: bool = False
) -> Tuple[int, int, str, bytes]:
    """
    Preprocess image dengan enhancement khusus untuk deteksi jentik nyamuk
    
    Pipeline:
    1. Resize jika terlalu besar
    2. Grayscale & Noise Reduction - menghilangkan grain sensor ESP32-CAM
    3. CLAHE - memperkuat kontras jentik terhadap air secara lokal
    4. Sharpening - menegaskan tepi jentik agar tidak "berawan"
    5. Morphological Operations (optional) - menebalkan jentik yang tipis
    
    Args:
        input_path: Path ke gambar input
        output_path: Path untuk menyimpan gambar preprocessed
        enhance_for_larvae: Aktifkan pipeline enhancement jentik
        apply_denoise: Aktifkan noise reduction
        apply_clahe_enhancement: Aktifkan CLAHE
        apply_sharp: Aktifkan sharpening
        apply_morphology: Aktifkan morphological operations
        denoise_strength: Kekuatan noise reduction (5-20, default: 10)
        clahe_clip_limit: Clip limit CLAHE (1.0-4.0, default: 2.5)
        sharpening_method: 'laplacian' atau 'unsharp'
        morph_operation: 'dilate', 'erode', 'open', 'close'
        morph_iterations: Jumlah iterasi morphological operation
        save_as_grayscale: Simpan sebagai grayscale (True) atau RGB (False)
    
    Returns: (width, height, checksum, image_data)
    """
    # Ensure output directory exists
    directory = os.path.dirname(output_path)
    ensure_directory_exists(directory)
    
    # Read image dengan OpenCV
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Could not read image from {input_path}")
    
    # Resize if too large (max 1024x1024) - penting untuk performa
    max_size = 1024
    height, width = image.shape[:2]
    if width > max_size or height > max_size:
        scale = min(max_size / width, max_size / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    if enhance_for_larvae:
        # Apply full larvae enhancement pipeline
        enhanced = enhance_larvae_visibility(
            image,
            apply_denoise=apply_denoise,
            apply_clahe_enhancement=apply_clahe_enhancement,
            apply_sharp=apply_sharp,
            apply_morphology=apply_morphology,
            denoise_strength=denoise_strength,
            clahe_clip_limit=clahe_clip_limit,
            sharpening_method=sharpening_method,
            morph_operation=morph_operation,
            morph_iterations=morph_iterations
        )
        
        if save_as_grayscale:
            # Simpan sebagai grayscale
            output_image = enhanced
        else:
            # Convert kembali ke RGB (3 channel) untuk kompatibilitas
            output_image = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    else:
        # Tanpa enhancement, hanya resize
        output_image = image
    
    # Save preprocessed image
    cv2.imwrite(output_path, output_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # Get final dimensions
    if len(output_image.shape) == 2:
        height, width = output_image.shape
    else:
        height, width = output_image.shape[:2]
    
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
