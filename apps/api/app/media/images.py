import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings


class InvalidImageError(ValueError):
    pass


def normalize_image(content: bytes) -> tuple[bytes, int, int]:
    if not content:
        raise InvalidImageError("The uploaded file is empty.")
    if len(content) > settings.media_max_upload_bytes:
        raise InvalidImageError("The image exceeds the upload size limit.")

    Image.MAX_IMAGE_PIXELS = settings.media_max_image_pixels
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise InvalidImageError("Only JPEG, PNG and WebP images are supported.")
                if getattr(source, "n_frames", 1) != 1:
                    raise InvalidImageError("Animated images are not supported.")
                source.verify()
            with Image.open(io.BytesIO(content)) as source:
                if getattr(source, "n_frames", 1) != 1:
                    raise InvalidImageError("Animated images are not supported.")
                image = ImageOps.exif_transpose(source)
                if image.width * image.height > settings.media_max_image_pixels:
                    raise InvalidImageError("The image dimensions exceed the allowed limit.")
                if image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGBA" if "transparency" in image.info else "RGB")
                output = io.BytesIO()
                image.save(output, format="WEBP", quality=82, method=6)
                normalized = output.getvalue()
                if len(normalized) > settings.media_max_upload_bytes:
                    raise InvalidImageError("The processed image exceeds the upload size limit.")
                return normalized, image.width, image.height
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InvalidImageError("The uploaded file is not a valid supported image.") from exc
