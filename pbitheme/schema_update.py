"""Check whether a newer Power BI report theme JSON schema is available upstream.

The schema is bundled by filename (``reportThemeSchema-<version>.json``) from
Microsoft's ``powerbi-desktop-samples`` repository. This module fetches the list
of schema files in that repo and reports the newest version, so the app can tell
the user whether the bundled schema is current.

It is GUI-free and uses only the standard library (``urllib``), so it is easy to
test offline: all network access goes through :func:`_http_get`, which tests
monkeypatch.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple

from . import __version__
from .validate import schema_version

# GitHub contents API for the schema folder, and the human-facing page.
SCHEMA_CONTENTS_URL = (
    "https://api.github.com/repos/microsoft/powerbi-desktop-samples/"
    "contents/Report%20Theme%20JSON%20Schema"
)
UPSTREAM_PAGE_URL = (
    "https://github.com/microsoft/powerbi-desktop-samples/tree/main/"
    "Report%20Theme%20JSON%20Schema"
)

_SCHEMA_NAME_RE = re.compile(r"^reportThemeSchema-([0-9.]+)\.json$", re.IGNORECASE)


def _version_tuple(name_or_version: str) -> Tuple[int, ...]:
    """Turn ``reportThemeSchema-2.157.json`` (or ``"2.157"``) into ``(2, 157)``.

    Returns ``(0,)`` for anything that doesn't parse, so comparisons stay safe.
    """
    stem = name_or_version
    m = _SCHEMA_NAME_RE.match(name_or_version)
    if m:
        stem = m.group(1)
    try:
        return tuple(int(p) for p in stem.split("."))
    except (ValueError, AttributeError):
        return (0,)


def _http_get(url: str, timeout: float = 10.0) -> bytes:
    """Fetch *url* and return the raw body. The single network seam (tests patch)."""
    import urllib.request

    req = urllib.request.Request(
        url,
        headers={
            # GitHub's API rejects requests without a User-Agent.
            "User-Agent": f"PBiThemeCreator/{__version__}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_latest(contents_json: bytes) -> Optional[str]:
    """Return the newest schema version string from a GitHub contents payload.

    The payload is the JSON array the contents API returns for the folder; each
    entry has a ``name``. Non-schema files are ignored. Returns ``None`` when no
    schema file is present or the payload can't be parsed.
    """
    try:
        entries = json.loads(contents_json)
    except (ValueError, TypeError):
        return None
    if not isinstance(entries, list):
        return None

    versions = []
    for entry in entries:
        name = entry.get("name") if isinstance(entry, dict) else None
        if isinstance(name, str) and _SCHEMA_NAME_RE.match(name):
            versions.append(_SCHEMA_NAME_RE.match(name).group(1))
    if not versions:
        return None
    return max(versions, key=_version_tuple)


def check_for_update(bundled: Optional[str] = None, timeout: float = 10.0) -> Dict[str, Any]:
    """Compare the bundled schema version against the newest upstream one.

    Returns a dict ``{bundled, latest, update_available, error}``. Never raises:
    any network or parse failure is reported in ``error`` (with ``latest`` None).
    """
    if bundled is None:
        bundled = schema_version()
    result: Dict[str, Any] = {
        "bundled": bundled,
        "latest": None,
        "update_available": False,
        "error": None,
    }
    try:
        latest = parse_latest(_http_get(SCHEMA_CONTENTS_URL, timeout=timeout))
    except Exception as exc:  # noqa: BLE001 - report any failure, don't crash the UI
        result["error"] = str(exc) or exc.__class__.__name__
        return result

    if latest is None:
        result["error"] = "Could not read the schema list from the source."
        return result

    result["latest"] = latest
    if bundled is not None:
        result["update_available"] = _version_tuple(latest) > _version_tuple(bundled)
    return result


def main() -> int:
    """Print the update-check result (``python -m pbitheme.schema_update``)."""
    info = check_for_update()
    if info["error"]:
        print(f"Could not check for updates: {info['error']}")
        return 1
    if info["update_available"]:
        print(f"Update available: bundled v{info['bundled']}, latest v{info['latest']}")
    else:
        print(f"Up to date (v{info['bundled']}).")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
