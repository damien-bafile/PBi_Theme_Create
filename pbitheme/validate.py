"""Validate a theme against the official Power BI report theme JSON schema.

The schema (Draft 7) is bundled from Microsoft's ``powerbi-desktop-samples``
repository.  ``jsonschema`` is an optional dependency: if it is not installed
the validator degrades gracefully and says so instead of raising.
"""

from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, List, Optional, Tuple

_SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schema")


def bundled_schema_path() -> Optional[str]:
    """Return the path of the newest bundled ``reportThemeSchema-*.json``."""
    matches = glob.glob(os.path.join(_SCHEMA_DIR, "reportThemeSchema-*.json"))
    if not matches:
        return None

    def version_key(path: str) -> Tuple[int, ...]:
        stem = os.path.basename(path).split("-", 1)[-1].rsplit(".json", 1)[0]
        try:
            return tuple(int(p) for p in stem.split("."))
        except ValueError:
            return (0,)

    return max(matches, key=version_key)


def schema_version() -> Optional[str]:
    path = bundled_schema_path()
    if not path:
        return None
    return os.path.basename(path).split("-", 1)[-1].rsplit(".json", 1)[0]


def validate_theme(theme: Dict[str, Any]) -> List[str]:
    """Validate *theme* (a dict) against the bundled schema.

    Returns a list of human-readable error strings; an empty list means the
    theme conforms.  Raises :class:`RuntimeError` only if validation cannot be
    performed at all (missing dependency or missing schema).
    """
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "The 'jsonschema' package is required to validate themes.\n"
            "Install it with:  pip install jsonschema"
        ) from exc

    path = bundled_schema_path()
    if not path:
        raise RuntimeError("No bundled Power BI theme schema was found.")

    with open(path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(theme), key=lambda e: list(e.path))

    messages: List[str] = []
    for err in errors:
        location = "/".join(str(p) for p in err.path) or "(root)"
        messages.append(f"[{location}] {err.message}")
    return messages
