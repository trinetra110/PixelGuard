import os
import hashlib
import io
import base64
from PIL import Image, ImageChops, ImageDraw, ImageEnhance
from PIL.ExifTags import TAGS

def compute_file_hash(file_bytes_or_path):
    """Compute SHA-256 hash from file path or bytes."""
    hasher = hashlib.sha256()
    if isinstance(file_bytes_or_path, (bytes, bytearray)):
        hasher.update(file_bytes_or_path)
    else:
        with open(file_bytes_or_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
    return hasher.hexdigest()

def extract_metadata_from_image(img, file_size=0):
    """Extract format, dimensions, size, and EXIF tags safely."""
    metadata = {
        "format": img.format or "UNKNOWN",
        "mode": img.mode,
        "width": img.width,
        "height": img.height,
        "dimensions": f"{img.width} × {img.height}",
        "file_size": file_size,
        "file_size_formatted": format_bytes(file_size),
        "exif": {}
    }

    try:
        exif_data = img._getexif() if hasattr(img, "_getexif") else None
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, str(tag))
                # Convert non-serializable objects to string
                if isinstance(value, (bytes, bytearray)):
                    try:
                        value = value.decode("utf-8", errors="replace")
                    except Exception:
                        value = str(value)
                elif not isinstance(value, (str, int, float, bool, list, dict)):
                    value = str(value)
                metadata["exif"][str(tag_name)] = value
    except Exception:
        pass

    return metadata

def format_bytes(size):
    """Human readable file size format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def generate_tamper_diff(img1, img2, max_sample_pixels=50):
    """
    Perform pixel-level comparison, returning:
    - total modified pixel count
    - percentage modified
    - bounding box [x1, y1, x2, y2]
    - sample coordinates
    - base64 encoded difference heatmap and highlighted image
    """
    # Normalize images to RGB
    img1_rgb = img1.convert("RGB")
    img2_rgb = img2.convert("RGB")

    if img1_rgb.size != img2_rgb.size:
        return {
            "dimension_mismatch": True,
            "message": f"Images have different dimensions: ({img1.width}×{img1.height}) vs ({img2.width}×{img2.height})"
        }

    width, height = img1_rgb.size
    total_pixels = width * height

    # Fast difference calculation via ImageChops
    diff = ImageChops.difference(img1_rgb, img2_rgb)
    bbox = diff.getbbox()

    if not bbox:
        return {
            "has_tampering": False,
            "modified_pixel_count": 0,
            "modified_percentage": 0.0,
            "sample_pixels": [],
            "bbox": None,
            "diff_preview_b64": None,
            "highlight_overlay_b64": None
        }

    # Extract changed pixels
    modified_pixels = []
    # Scan within bounding box for efficiency
    x_start, y_start, x_end, y_end = bbox
    img1_pixels = img1_rgb.load()
    img2_pixels = img2_rgb.load()

    total_modified = 0
    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            if img1_pixels[x, y] != img2_pixels[x, y]:
                total_modified += 1
                if len(modified_pixels) < max_sample_pixels:
                    modified_pixels.append({
                        "x": x,
                        "y": y,
                        "orig_rgb": list(img1_pixels[x, y]),
                        "suspect_rgb": list(img2_pixels[x, y])
                    })

    percentage_modified = (total_modified / total_pixels) * 100

    # 1. Create enhanced visual difference map (high-contrast neon heatmap)
    # Amplify difference so subtle 1-bit changes glow intensely
    diff_enhanced = ImageEnhance.Brightness(diff).enhance(4.0)
    diff_enhanced = ImageEnhance.Contrast(diff_enhanced).enhance(2.5)

    # 2. Create highlighted overlay on top of suspect image
    highlight_img = img2_rgb.copy()
    draw = ImageDraw.Draw(highlight_img, "RGBA")

    # Draw expanded bounding box in glowing neon red/magenta
    pad = 4
    expanded_bbox = (
        max(0, x_start - pad),
        max(0, y_start - pad),
        min(width - 1, x_end + pad),
        min(height - 1, y_end + pad)
    )
    # Clean architectural marker in muted terracotta
    draw.rectangle(expanded_bbox, outline="#8C5159", width=2)
    # Add subtle cross-bracket if area is small
    if (x_end - x_start) < 20 and (y_end - y_start) < 20:
        center_x = (x_start + x_end) // 2
        center_y = (y_start + y_end) // 2
        d = 8
        draw.line([(center_x - d, center_y), (center_x + d, center_y)], fill="#8C5159", width=1)
        draw.line([(center_x, center_y - d), (center_x, center_y + d)], fill="#8C5159", width=1)

    # Convert to base64 for direct browser rendering
    diff_b64 = image_to_base64(diff_enhanced, "PNG")
    highlight_b64 = image_to_base64(highlight_img, "JPEG")

    return {
        "has_tampering": True,
        "dimension_mismatch": False,
        "modified_pixel_count": total_modified,
        "total_pixels": total_pixels,
        "modified_percentage": round(percentage_modified, 4),
        "bbox": list(bbox),
        "sample_pixels": modified_pixels,
        "diff_preview_b64": f"data:image/png;base64,{diff_b64}",
        "highlight_overlay_b64": f"data:image/jpeg;base64,{highlight_b64}"
    }

def image_to_base64(img, format="PNG"):
    """Convert a PIL image to base64 string."""
    buffered = io.BytesIO()
    img.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
