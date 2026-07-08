from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import ExifTags, Image


TAGS = {value: key for key, value in ExifTags.TAGS.items()}
GPS_TAGS = ExifTags.GPSTAGS


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except TypeError:
        return float(value[0]) / float(value[1])


def _gps_to_decimal(values: Any, ref: str) -> float | None:
    try:
        degrees = _to_float(values[0])
        minutes = _to_float(values[1])
        seconds = _to_float(values[2])
    except (TypeError, ValueError, ZeroDivisionError, IndexError):
        return None
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in {"S", "W"}:
        decimal = -decimal
    return round(decimal, 6)


def _stringify(value: Any) -> str:
    if isinstance(value, bytes):
        try:
            return value.decode(errors="replace")
        except Exception:
            return repr(value)
    if isinstance(value, tuple):
        return ", ".join(_stringify(item) for item in value)
    return str(value)


def extract_exif(file_bytes: bytes) -> dict[str, Any]:
    try:
        image = Image.open(BytesIO(file_bytes))
        exif = image.getexif()
    except Exception as exc:
        return {
            "metadata": [],
            "gps": None,
            "camera_model": None,
            "timestamp": None,
            "warnings": [f"Could not read image metadata: {exc}"],
        }

    if not exif:
        return {
            "metadata": [],
            "gps": None,
            "camera_model": None,
            "timestamp": None,
            "warnings": ["No EXIF metadata found in this image."],
        }

    metadata = []
    gps_raw = None
    camera_model = None
    timestamp = None
    for tag_id, value in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        if tag_name == "GPSInfo":
            gps_raw = value
            continue
        display_value = _stringify(value)
        metadata.append({"Tag": tag_name, "Value": display_value})
        if tag_name in {"Model", "CameraModel"}:
            camera_model = display_value
        if tag_name in {"DateTimeOriginal", "DateTimeDigitized", "DateTime"} and not timestamp:
            timestamp = display_value

    gps = None
    if gps_raw:
        gps_decoded = {}
        for gps_id, gps_value in gps_raw.items():
            gps_decoded[GPS_TAGS.get(gps_id, gps_id)] = gps_value
        latitude = _gps_to_decimal(gps_decoded.get("GPSLatitude"), gps_decoded.get("GPSLatitudeRef", "N"))
        longitude = _gps_to_decimal(gps_decoded.get("GPSLongitude"), gps_decoded.get("GPSLongitudeRef", "E"))
        if latitude is not None and longitude is not None:
            gps = {"latitude": latitude, "longitude": longitude}
            metadata.append({"Tag": "GPSLatitude", "Value": str(latitude)})
            metadata.append({"Tag": "GPSLongitude", "Value": str(longitude)})

    warnings = []
    if gps:
        warnings.append("GPS metadata is present and may expose a location.")
    if camera_model:
        warnings.append("Camera model metadata is present and may expose source identity.")
    if timestamp:
        warnings.append("Timestamp metadata is present and may reveal when the image was captured.")

    return {
        "metadata": sorted(metadata, key=lambda row: row["Tag"]),
        "gps": gps,
        "camera_model": camera_model,
        "timestamp": timestamp,
        "warnings": warnings,
    }
