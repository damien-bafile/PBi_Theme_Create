"""Object model for a Power BI report theme.

This module is completely independent of any GUI toolkit so that the theme
can be created, serialised and validated from scripts as well as from the Qt
application.  Everything is expressed with small, well encapsulated classes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

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

# All valid Power BI visual types that can be customised in a theme.
# Each tuple is (JSON key, human label).
VISUAL_TYPES: List[tuple[str, str]] = [
    ("*", "All visuals (wildcard)"),
    ("areaChart", "Area Chart"),
    ("actionButton", "Action Button"),
    ("azureMapVisual", "Azure Maps"),
    ("barChart", "Bar Chart"),
    ("basicShape", "Basic Shape"),
    ("card", "Card"),
    ("clusteredBarChart", "Clustered Bar Chart"),
    ("clusteredColumnChart", "Clustered Column Chart"),
    ("columnChart", "Column Chart"),
    ("decompositionTreeVisual", "Decomposition Tree"),
    ("donutChart", "Donut Chart"),
    ("filledMap", "Filled Map"),
    ("funnel", "Funnel"),
    ("gauge", "Gauge"),
    ("hundredPercentStackedBarChart", "100% Stacked Bar Chart"),
    ("hundredPercentStackedColumnChart", "100% Stacked Column Chart"),
    ("image", "Image"),
    ("keyDriversVisual", "Key Drivers"),
    ("kpi", "KPI"),
    ("lineChart", "Line Chart"),
    ("lineClusteredColumnComboChart", "Line & Clustered Column Chart"),
    ("lineStackedColumnComboChart", "Line & Stacked Column Chart"),
    ("map", "Map"),
    ("matrix", "Matrix"),
    ("multiRowCard", "Multi-row Card"),
    ("pivotTable", "Pivot Table"),
    ("pieChart", "Pie Chart"),
    ("pythonVisual", "Python Visual"),
    ("qnaVisual", "Q&A"),
    ("ribbonChart", "Ribbon Chart"),
    ("rVisual", "R Visual"),
    ("scatterChart", "Scatter Chart"),
    ("shapeMap", "Shape Map"),
    ("slicer", "Slicer"),
    ("smartNarrative", "Smart Narrative"),
    ("table", "Table"),
    ("tableEx", "Table (Extended)"),
    ("textbox", "Text Box"),
    ("treemap", "Treemap"),
    ("waterfallChart", "Waterfall Chart"),
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
            # Power BI's schema constrains font sizes to 8-60.
            data["fontSize"] = max(8, min(60, int(self.font_size)))
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
    # (attribute, theme JSON key, UI label, default) -- structural colour classes.
    # These map to Power BI's named colour classes and sentiment colours, all of
    # which are top-level theme properties.
    STRUCTURAL_FIELDS = [
        ("foreground", "foreground", "Foreground", "#252423"),
        ("second_level", "secondLevelElements", "Secondary text", "#605E5C"),
        ("third_level", "thirdLevelElements", "Gridlines / grid", "#F3F2F1"),
        ("fourth_level", "fourthLevelElements", "Dimmed / category", "#B3B0AD"),
        ("background", "background", "Background", "#FFFFFF"),
        ("secondary_background", "secondaryBackground", "Secondary background", "#C8C6C4"),
        ("table_accent", "tableAccent", "Table accent", "#118DFF"),
        ("good", "good", "Good", "#1AAB40"),
        ("neutral", "neutral", "Neutral", "#F2C811"),
        ("bad", "bad", "Bad", "#D64550"),
    ]

    # Conditional-formatting gradient colours (also top-level theme properties).
    GRADIENT_FIELDS = [
        ("gradient_min", "minimum", "Minimum", "#DEEFFF"),
        ("gradient_center", "center", "Center", "#D9B300"),
        ("gradient_max", "maximum", "Maximum", "#118DFF"),
        ("gradient_null", "null", "Null / N/A", "#FF7F48"),
    ]

    def __init__(self, name: str = "My Theme") -> None:
        self.name: str = name
        self.data_colors: List[str] = list(DEFAULT_DATA_COLORS)
        for attr, _key, _label, default in self.STRUCTURAL_FIELDS + self.GRADIENT_FIELDS:
            setattr(self, attr, default)
        self.text_classes: Dict[str, TextClass] = _default_text_classes()
        self.visual_styles: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Build the JSON-ready dict, omitting empty/optional values."""
        theme: Dict[str, Any] = {"name": self.name or "My Theme"}

        colors = [normalise_hex(c) for c in self.data_colors if is_valid_hex(c)]
        if colors:
            theme["dataColors"] = colors

        for attr, key, _label, _default in self.STRUCTURAL_FIELDS + self.GRADIENT_FIELDS:
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

        if self.visual_styles:
            # Translate the app's internal formatting into valid Power BI cards.
            from .theme_export import build_visual_styles
            visual_styles = build_visual_styles(self.visual_styles)
            if visual_styles:
                theme["visualStyles"] = visual_styles

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

        for attr, key, _label, _default in cls.STRUCTURAL_FIELDS + cls.GRADIENT_FIELDS:
            if key in data:
                setattr(theme, attr, str(data[key]))

        raw_classes = data.get("textClasses")
        if isinstance(raw_classes, dict):
            theme.text_classes = {
                name: TextClass.from_dict(name, value)
                for name, value in raw_classes.items()
                if isinstance(value, dict)
            }

        if isinstance(data.get("visualStyles"), dict):
            # Convert real Power BI cards back into the app's internal form so the
            # editor's per-visual formatter repopulates on open/import.
            from .theme_export import import_visual_styles
            theme.visual_styles = import_visual_styles(data["visualStyles"])

        return theme

    @classmethod
    def load(cls, path: str) -> "PowerBITheme":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    # ------------------------------------------------------------------ #
    # Visual styles
    # ------------------------------------------------------------------ #
    def is_visual_customised(self, visual_key: str) -> bool:
        """Return True if *visual_key* or the wildcard "*" has style overrides."""
        return bool(
            self.visual_styles.get(visual_key)
            or self.visual_styles.get("*")
        )


# ====================================================================== #
# Visual style builders and unpackers (for interactive editor)
# ====================================================================== #

LEGEND_POSITIONS: List[str] = [
    "Top", "Bottom", "Left", "Right",
    "TopCenter", "BottomCenter", "LeftCenter", "RightCenter"
]

def _solid_color(hex_color: str) -> Dict[str, Any]:
    """Wrap a hex color in the Power BI solid color format."""
    return {"solid": {"color": normalise_hex(hex_color)}}


def _first(items: Any) -> Dict[str, Any]:
    """Extract first dict from a list, or return empty dict."""
    return items[0] if isinstance(items, list) and items and isinstance(items[0], dict) else {}


def _extract_solid_color(value: Any, default: str) -> str:
    """Extract and normalise a hex color from a solid-color object."""
    color = (value or {}).get("solid", {}).get("color") if isinstance(value, dict) else None
    if isinstance(color, str):
        c = color if color.startswith("#") else f"#{color}"
        if is_valid_hex(c):
            return normalise_hex(c)
    return default


def build_background_object(show: bool, color: str, transparency: int) -> List[Dict[str, Any]]:
    """Build a background visual-style object from picker state."""
    return [{"show": show, "color": _solid_color(color), "transparency": int(transparency)}]


def build_border_object(show: bool, color: str, radius: int = 0, width: int = 1) -> List[Dict[str, Any]]:
    """Build a border visual-style object from picker state."""
    return [{"show": show, "color": _solid_color(color), "radius": int(radius), "width": int(width)}]


def build_drop_shadow_object(show: bool, color: str) -> List[Dict[str, Any]]:
    """Build a drop-shadow visual-style object from picker state."""
    return [{"show": show, "color": _solid_color(color), "position": "Outer"}]


def build_visual_header_object(show: bool, background: str, foreground: str) -> List[Dict[str, Any]]:
    """Build a visual-header visual-style object from picker state."""
    return [{"show": show, "background": _solid_color(background), "foreground": _solid_color(foreground)}]


def build_subtitle_object(show: bool, text: str, color: str, font_size: int) -> List[Dict[str, Any]]:
    """Build a subtitle visual-style object from picker state."""
    obj: Dict[str, Any] = {"show": show, "fontColor": _solid_color(color), "fontSize": int(font_size)}
    if text:
        obj["text"] = text
    return [obj]


def build_padding_object(padding: int) -> List[Dict[str, Any]]:
    """Build a padding visual-style object (uniform on all sides)."""
    p = int(padding)
    return [{"top": p, "bottom": p, "left": p, "right": p}]


def build_title_object(show: bool, font_face: str, font_size: int, color: str) -> List[Dict[str, Any]]:
    """Build a title visual-style object from picker state."""
    return [{"show": show, "fontColor": _solid_color(color), "fontSize": int(font_size), "fontFamily": font_face}]


def build_data_labels_object(show: bool, color: str, font_size: int) -> List[Dict[str, Any]]:
    """Build a data-labels visual-style object from picker state."""
    return [{"show": show, "color": _solid_color(color), "fontSize": int(font_size)}]


def build_legend_object(show: bool, position: str, color: str) -> List[Dict[str, Any]]:
    """Build a legend visual-style object from picker state."""
    return [{"show": show, "position": position, "labelColor": _solid_color(color)}]


def unpack_background_object(obj: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Extract background picker state from an existing visual's * entry."""
    p = _first(obj.get("background", {}))
    return (
        bool(p.get("show", True)),
        _extract_solid_color(p.get("color"), "#FFFFFF"),
        int(p.get("transparency", 0) or 0)
    )


def unpack_border_object(obj: Dict[str, Any]) -> Tuple[bool, str, int, int]:
    """Extract border picker state from an existing visual's * entry."""
    p = _first(obj.get("border", {}))
    return (
        bool(p.get("show", True)),
        _extract_solid_color(p.get("color"), "#000000"),
        int(p.get("radius", 0) or 0),
        int(p.get("width", 1) or 1),
    )


def unpack_drop_shadow_object(obj: Dict[str, Any]) -> Tuple[bool, str]:
    """Extract drop-shadow picker state from an existing visual's * entry."""
    p = _first(obj.get("dropShadow", {}))
    return (
        bool(p.get("show", True)),
        _extract_solid_color(p.get("color"), "#000000"),
    )


def unpack_visual_header_object(obj: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Extract visual-header picker state from an existing visual's * entry."""
    p = _first(obj.get("visualHeader", {}))
    return (
        bool(p.get("show", True)),
        _extract_solid_color(p.get("background"), "#FFFFFF"),
        _extract_solid_color(p.get("foreground"), "#605E5C"),
    )


def unpack_subtitle_object(obj: Dict[str, Any]) -> Tuple[bool, str, str, int]:
    """Extract subtitle picker state from an existing visual's * entry."""
    p = _first(obj.get("subTitle", {}))
    return (
        bool(p.get("show", True)),
        str(p.get("text", "")),
        _extract_solid_color(p.get("fontColor"), "#605E5C"),
        int(p.get("fontSize", 10) or 10),
    )


def unpack_padding_object(obj: Dict[str, Any]) -> int:
    """Extract uniform padding (top) from an existing visual's * entry."""
    p = _first(obj.get("padding", {}))
    return int(p.get("top", 0) or 0)


def unpack_title_object(obj: Dict[str, Any]) -> Tuple[bool, str, int, str]:
    """Extract title picker state from an existing visual's * entry."""
    p = _first(obj.get("title", {}))
    return (
        bool(p.get("show", True)),
        str(p.get("fontFamily", "Segoe UI")),
        int(p.get("fontSize", 12) or 12),
        _extract_solid_color(p.get("fontColor"), "#252423")
    )


def unpack_data_labels_object(obj: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Extract data-labels picker state from an existing visual's * entry."""
    p = _first(obj.get("labels", {}))
    return (
        bool(p.get("show", False)),
        _extract_solid_color(p.get("color"), "#252423"),
        int(p.get("fontSize", 9) or 9)
    )


def unpack_legend_object(obj: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Extract legend picker state from an existing visual's * entry."""
    p = _first(obj.get("legend", {}))
    return (
        bool(p.get("show", True)),
        str(p.get("position", "Top")),
        _extract_solid_color(p.get("labelColor"), "#252423")
    )


def merge_visual_style_entry(base: Dict[str, Any], overrides: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Merge structured-picker overrides with the advanced-JSON base dict.

    The base dict (parsed from the advanced-JSON box) is copied, then for each
    key present in overrides, that key fully replaces the one in the base.
    Keys absent from overrides pass through from base unchanged.
    """
    result = dict(base)
    result.update(overrides)
    return result
