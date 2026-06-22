import uuid
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps

PROPERTY_PICS_DIR = Path("static/uploads/properties")

def process_property_image(content: bytes) -> str:
    """
    Synchronous, CPU-bound image processing function.
    Resizes property photos for optimal Web/Mobile viewing without cropping.
    """
    with Image.open(BytesIO(content)) as original:
        # Auto-orient based on camera EXIF data (fixes sideways phone photos)
        img = ImageOps.exif_transpose(original)

        # Ensure image is in RGB mode (drops transparency/alpha channels)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        # 1280x1280 is a bounding box. 
        # A 4000x2000 image becomes 1280x640 (aspect ratio is preserved!)
        img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)

        # Generate unique filename using WebP
        filename = f"{uuid.uuid4().hex}.webp"
        filepath = PROPERTY_PICS_DIR / filename

        # Ensure directory exists
        PROPERTY_PICS_DIR.mkdir(parents=True, exist_ok=True)

        # Save as optimized WebP
        img.save(filepath, "WEBP", quality=80)

    return filename