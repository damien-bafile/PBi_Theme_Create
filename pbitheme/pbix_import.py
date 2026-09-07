"""Extract theme data from Power BI report files (.pbix, .pbit)."""

import json
import zipfile
from pathlib import Path
from typing import Optional

from .model import PowerBITheme


class NoThemeFoundError(Exception):
    """Raised when a .pbix/.pbit file contains no custom theme data."""

    pass


def extract_theme_from_pbix(path: str) -> PowerBITheme:
    """Extract a Power BI theme from a .pbix or .pbit file.

    Searches for:
    1. A custom theme resource in Report/StaticResources/RegisteredResources/*.json
    2. An inline theme override under the "theme" key in Report/Layout

    Raises NoThemeFoundError if neither source yields theme data.
    """
    path_obj = Path(path)

    try:
        with zipfile.ZipFile(path_obj, "r") as zf:
            # Try to find a registered custom theme resource
            theme = _extract_from_registered_resources(zf)
            if theme:
                return theme

            # Fall back to inline theme overrides in Report/Layout
            theme = _extract_from_layout(zf)
            if theme:
                return theme

    except zipfile.BadZipFile as exc:
        raise ValueError(f"Not a valid Power BI file: {path}") from exc

    raise NoThemeFoundError(
        "This file doesn't use a custom theme — only Power BI's built-in "
        "theme is applied."
    )


def _extract_from_registered_resources(zf: zipfile.ZipFile) -> Optional[PowerBITheme]:
    """Look for theme JSON files in Report/StaticResources/RegisteredResources/."""
    try:
        resource_path = "Report/StaticResources/RegisteredResources/"
        names = zf.namelist()
        theme_files = [n for n in names if n.startswith(resource_path) and n.endswith(".json")]

        if not theme_files:
            return None

        theme_file = theme_files[0]
        try:
            data = json.loads(zf.read(theme_file).decode("utf-8"))
            return PowerBITheme.from_dict(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(
                f"Could not parse theme resource {theme_file}: {exc}"
            ) from exc

    except KeyError:
        return None


def _extract_from_layout(zf: zipfile.ZipFile) -> Optional[PowerBITheme]:
    """Look for inline theme overrides in Report/Layout."""
    try:
        layout_bytes = zf.read("Report/Layout")
    except KeyError:
        return None

    try:
        layout_data = json.loads(layout_bytes.decode("utf-16-le", errors="ignore"))
    except json.JSONDecodeError:
        return None

    if not isinstance(layout_data, dict):
        return None

    theme_data = layout_data.get("theme")
    if not isinstance(theme_data, dict):
        return None

    try:
        return PowerBITheme.from_dict(theme_data)
    except Exception as exc:
        raise ValueError(f"Could not parse inline theme data: {exc}") from exc
