"""Helpers for stable, human-readable camera codes used when syncing to CCTV Master."""

from __future__ import annotations

import re

CAMERA_CODE_PATTERN = re.compile(r"^CAM-\d{2,}$")


def format_camera_code(sequence: int) -> str:
    """Format sequence number as CAM-01, CAM-02, ... CAM-99, CAM-100, ..."""
    if sequence < 1:
        sequence = 1
    if sequence < 100:
        return f"CAM-{sequence:02d}"
    return f"CAM-{sequence}"


def normalize_camera_code(value: str) -> str:
    """Uppercase and trim a user-supplied camera code."""
    return value.strip().upper()


def is_valid_camera_code(value: str) -> bool:
    return bool(CAMERA_CODE_PATTERN.match(normalize_camera_code(value)))
