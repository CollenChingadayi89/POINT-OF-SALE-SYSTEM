# utils/barcode_utils.py
import random
import logging
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File

logger = logging.getLogger(__name__)

def generate_barcode_base(branch_id):
    """Generate 9-digit barcode: 3 branch digits + 6 random digits"""
    try:
        branch_part = str(branch_id).zfill(3)[:3]
        random_part = str(random.randint(100000, 999999))
        return f"{branch_part}{random_part}"
    except Exception as e:
        logger.error(f"Barcode generation failed: {str(e)}")
        raise ValueError("Failed to generate barcode")

def generate_barcode_image(barcode_base):
    """
    Generate barcode image using python-barcode
    The library automatically handles CODE128 checksum internally
    """
    try:
        # Initialize with proper settings
        writer = ImageWriter()
        writer.set_options({
            'module_width': 0.2,
            'module_height': 15,
            'font_size': 10,
            'text_distance': 5
        })
        
        # Generate CODE128 barcode (automatically adds internal checksum)
        code128 = barcode.get_barcode_class('code128')
        code = code128(barcode_base, writer=writer)
        
        # Save to buffer
        buffer = BytesIO()
        code.write(buffer)
        buffer.seek(0)
        return File(buffer)
    except Exception as e:
        logger.error(f"Barcode image generation failed: {str(e)}")
        raise ValueError("Failed to generate barcode image")