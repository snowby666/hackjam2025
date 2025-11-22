"""Utility helper functions"""

import base64
import re
from typing import Optional
from PIL import Image
import io


def decode_base64_image(base64_string: str) -> bytes:
    """Decode base64 image string to bytes"""
    # Remove data URL prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    return base64.b64decode(base64_string)


def validate_image_format(image_bytes: bytes) -> bool:
    """Validate that image bytes are a valid image format"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        return True
    except Exception:
        return False


def get_image_dimensions(image_bytes: bytes) -> Optional[tuple]:
    """Get image dimensions (width, height)"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return img.size
    except Exception:
        return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove any non-alphanumeric characters except dots, hyphens, underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return sanitized[:255]  # Limit length

