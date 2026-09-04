"""Object model for a Power BI report theme.

This module is completely independent of any GUI toolkit so that the theme
can be created, serialised and validated from scripts as well as from the Qt
application.  Everything is expressed with small, well encapsulated classes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

# A default Power BI-flavoured qualitative palette.
DEFAULT_DATA_COLORS: List[str] = [
    "#118DFF",
    "#12239E",
    "#E66C37",
    "#6B007B",
    "#E044A7",
    "#744EC2",
    "#D9B300",
    "#D64550",
]

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def is_valid_hex(value: str) -> bool:
    """Return ``True`` when *value* is a ``#RGB`` or ``#RRGGBB`` colour."""
    return bool(_HEX_RE.match(value or ""))


def normalise_hex(value: str) -> str:
    """Normalise a colour to upper-case ``#RRGGBB`` form.

    Raises ``ValueError`` for anything that is not a valid hex colour.
    """
    if not is_valid_hex(value):
        raise ValueError(f"Not a valid hex colour: {value!r}")
    value = value.upper()
    if len(value) == 4:  # expand #RGB -> #RRGGBB
        r, g, b = value[1], value[2], value[3]
        value = f"#{r}{r}{g}{g}{b}{b}"
    return value


@dataclass
class TextClass:
    """A single Power BI text class (title, header, callout, label, ...)."""

    name: str
    font_face: str = "Segoe UI"
    font_size: int = 12
    color: str = "#252423"

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if self.font_face:
            data["fontFace"] = self.font_face
        if self.font_size:
            data["fontSize"] = int(self.font_size)
        if self.color:
            data["color"] = normalise_hex(self.color)
        return data

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "TextClass":
        return cls(
            name=name,
            font_face=data.get("fontFace", "Segoe UI"),
            font_size=int(data.get("fontSize", 12)),
            color=data.get("color", "#252423"),
        )


def _default_text_classes() -> Dict[str, TextClass]:
    return {
        "title": TextClass("title", "Segoe UI Semibold", 12, "#252423"),
        "header": TextClass("header", "Segoe UI Semibold", 12, "#252423"),
        "callout": TextClass("callout", "Segoe UI", 45, "#252423"),
        "label": TextClass("label", "Segoe UI", 10, "#252423"),
    }


class PowerBITheme:
    """In-memory representation of a Power BI report theme.

    The class owns all editable state and knows how to (de)serialise itself to
    the JSON structure that Power BI Desktop expects.
    """

    #: Structural colour fields -> (JSON key, human label, default value).
    STRUCTURAL_FIELDS = [
        ("foreground", "foreground", "Foreground", "#252423"),
        ("background", "background", "Background", "#FFFFFF"),
        ("table_accent", "tableAccent", "Table accent", "#118DFF"),
        ("good", "good", "Good", "#1AAB40"),
        ("neutral", "neutral", "Neutral", "#F2C811"),
        ("bad", "bad", "Bad", "#D64550"),
    ]

    def __init__(self, name: str = "My Theme") -> None:
        self.name: str = name
        self.data_colors: List[str] = list(DEFAULT_DATA_COLORS)
        self.foreground: str = "#252423"
        self.background: str = "#FFFFFF"
        self.table_accent: str = "#118DFF"
        self.good: str = "#1AAB40"
        self.neutral: str = "#F2C811"
        self.bad: str = "#D64550"
        self.text_classes: Dict[str, TextClass] = _default_text_classes()

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Build the JSON-ready dict, omitting empty/optional values."""
        theme: Dict[str, Any] = {"name": self.name or "My Theme"}

        colors = [normalise_hex(c) for c in self.data_colors if is_valid_hex(c)]
        if colors:
            theme["dataColors"] = colors

        for attr, key, _label, _default in self.STRUCTURAL_FIELDS:
            value = getattr(self, attr)
            if is_valid_hex(value):
                theme[key] = normalise_hex(value)

        text_classes = {
            name: tc.to_dict()
            for name, tc in self.text_classes.items()
            if tc.to_dict()
        }
        if text_classes:
            theme["textClasses"] = text_classes

        return theme

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str, indent: int = 2) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_json(indent=indent))

    # ------------------------------------------------------------------ #
    # Deserialisation
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PowerBITheme":
        theme = cls(name=data.get("name", "My Theme"))

        if isinstance(data.get("dataColors"), list):
            theme.data_colors = [str(c) for c in data["dataColors"]]

        for attr, key, _label, _default in cls.STRUCTURAL_FIELDS:
            if key in data:
                setattr(theme, attr, str(data[key]))

        raw_classes = data.get("textClasses")
        if isinstance(raw_classes, dict):
            theme.text_classes = {
                name: TextClass.from_dict(name, value)
                for name, value in raw_classes.items()
                if isinstance(value, dict)
            }

        return theme

    @classmethod
    def load(cls, path: str) -> "PowerBITheme":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
