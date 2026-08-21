import os
import re
from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image

ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
ALLOWED_IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/webp",
]
DEFAULT_MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB


def validate_phone_number(value: str) -> str:
    """
    Validates and normalizes contact phone numbers.
    Allows optional international dialing prefixes (+), hyphens, spaces, and parentheses.
    Ensures total digit count is between 7 and 15 digits.
    """
    if value is None:
        return ""

    clean_value = str(value).strip()
    if not clean_value:
        return ""

    # Check overall allowed character set
    if not re.match(r"^\+?[0-9\s\-\(\)\.]{7,25}$", clean_value):
        raise ValidationError("Enter a valid contact phone number containing digits and standard formatting characters.")

    # Extract pure digits
    digits = re.sub(r"\D", "", clean_value)
    if len(digits) < 7 or len(digits) > 15:
        raise ValidationError("Phone number must contain between 7 and 15 digits.")

    return clean_value


def validate_profile_image(file):
    """
    Validates uploaded user profile images for size, allowed formats, and structural integrity.
    """
    if not file:
        raise ValidationError("No image file provided.")

    # 1. File size checks
    if file.size == 0:
        raise ValidationError("The uploaded image file is empty.")

    max_size = getattr(settings, "MAX_PROFILE_IMAGE_SIZE", DEFAULT_MAX_IMAGE_SIZE)
    if file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        file_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f"Image file size exceeds the maximum allowed limit of {max_mb:.0f} MB (uploaded file is {file_mb:.2f} MB)."
        )

    # 2. File extension check
    filename = getattr(file, "name", "")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported image file format '{ext}'. Allowed formats: {', '.join([e.upper().lstrip('.') for e in ALLOWED_IMAGE_EXTENSIONS])}."
        )

    # 3. MIME Content-Type check (if provided by request)
    content_type = getattr(file, "content_type", None)
    if content_type and content_type.lower() not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError(
            f"Invalid image MIME type '{content_type}'. Must be JPEG, PNG, or WEBP."
        )

    # 4. Binary integrity verification via Pillow
    try:
        # Seek to start in case stream was partially read
        if hasattr(file, "seek"):
            file.seek(0)
        img = Image.open(file)
        img.verify()
        if img.format.lower() not in ["jpeg", "png", "webp"]:
            raise ValidationError(
                f"Image file format '{img.format}' is not supported. Allowed formats: JPEG, PNG, WEBP."
            )
        # Reset pointer after verify()
        if hasattr(file, "seek"):
            file.seek(0)
    except Exception as exc:
        if isinstance(exc, ValidationError):
            raise exc
        raise ValidationError("Uploaded file is corrupted or not a valid image.")

    return file
