"""Image processing service"""

from PIL import Image
import io
from typing import Optional, Tuple
from utils.helpers import decode_base64_image, validate_image_format, get_image_dimensions


class ImageProcessor:
    """Handle image processing operations"""
    
    @staticmethod
    async def process_screenshot(base64_image: str) -> dict:
        """Process uploaded screenshot"""
        try:
            # Decode base64
            image_bytes = decode_base64_image(base64_image)
            
            # Validate format
            if not validate_image_format(image_bytes):
                raise ValueError("Invalid image format")
            
            # Get dimensions
            dimensions = get_image_dimensions(image_bytes)
            
            # Get image metadata
            img = Image.open(io.BytesIO(image_bytes))
            format_type = img.format
            
            return {
                "image_bytes": image_bytes,
                "width": dimensions[0] if dimensions else None,
                "height": dimensions[1] if dimensions else None,
                "format": format_type,
                "size_bytes": len(image_bytes)
            }
        except Exception as e:
            raise ValueError(f"Image processing failed: {str(e)}")
    
    @staticmethod
    async def resize_image_if_needed(image_bytes: bytes, max_size: Tuple[int, int] = (2048, 2048)) -> bytes:
        """Resize image if it exceeds max dimensions"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                img.save(output, format=img.format or "PNG")
                return output.getvalue()
            
            return image_bytes
        except Exception as e:
            # If resize fails, return original
            return image_bytes

