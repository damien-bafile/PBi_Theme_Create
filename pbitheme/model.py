"""Object model for a Power BI report theme.

This module is completely independent of any GUI toolkit so that the theme
can be created, serialised and validated from scripts as well as from the Qt
application.  Everything is expressed with small, well encapsulated classes.

Besides the top-level colours and text classes it also models the detailed
``visualStyles`` block used by the deldersveld / MattRudy theme templates,
where each formatting card is an array with a single object and colours are
wrapped as ``{"solid": {"color": "#RRGGBB"}}``.
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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


def solid(color: str) -> Dict[str, Any]:
    """Wrap a hex colour in Power BI's ``{"solid": {"color": ...}}`` form."""
    return {"solid": {"color": normalise_hex(color)}}


def unwrap_solid(value: Any) -> Optional[str]:
    """Extract the hex colour from a ``{"solid": {"color": ...}}`` value."""
    try:
        return value["solid"]["color"]
    except (KeyError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Text classes (typography)
# --------------------------------------------------------------------------- #
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


def _default_text_classes() -> "OrderedDict[str, TextClass]":
    return OrderedDict(
        [
            ("title", TextClass("title", "Segoe UI Semibold", 12, "#252423")),
            ("header", TextClass("header", "Segoe UI Semibold", 12, "#252423")),
            ("callout", TextClass("callout", "Segoe UI", 45, "#252423")),
            ("label", TextClass("label", "Segoe UI", 10, "#252423")),
        ]
    )


# --------------------------------------------------------------------------- #
# visualStyles schema
# --------------------------------------------------------------------------- #
@dataclass
class PropSpec:
    """Describes a single formatting property inside a card."""

    key: str
    label: str
    kind: str  # bool | color | int | float | font | choice
    default: Any
    choices: Optional[List[tuple]] = None  # list of (value, label) for 'choice'

    def to_json_value(self, value: Any) -> Any:
        """Convert an editor value into its Power BI JSON representation."""
        if self.kind == "color":
            return solid(value)
        if self.kind == "int":
            return int(value)
        if self.kind == "float":
            return float(value)
        if self.kind == "bool":
            return bool(value)
        return value  # font / choice / text -> plain string

    def from_json_value(self, value: Any) -> Any:
        """Convert a Power BI JSON value back into an editor value."""
        if self.kind == "color":
            return unwrap_solid(value) or self.default
        return value


# Power BI requires labelDisplayUnits as an integer (schema oneOf enum).
_DISPLAY_UNITS = [
    (0, "Auto"),
    (1, "None"),
    (1000, "Thousands"),
    (1000000, "Millions"),
    (1000000000, "Billions"),
    (1000000000000, "Trillions"),
]

_ALIGNMENTS = [("left", "Left"), ("center", "Center"), ("right", "Right")]
# Table / matrix headers use a capitalised alignment enum (distinct from title).
_ALIGNMENTS_CAP = [("Left", "Left"), ("Center", "Center"), ("Right", "Right")]
_TITLE_ALIGNMENTS = [
    ("Auto", "Auto"),
    ("Left", "Left"),
    ("Center", "Center"),
    ("Right", "Right"),
]
# Slicer orientation is an integer enum in the current schema.
_ORIENTATION = [(1, "Vertical"), (2, "Horizontal"), (0, "Grid")]
_SUBTOTAL_POSITION = [("Top", "Top"), ("Bottom", "Bottom")]
# Built-in table / matrix style presets (internal names).
_TABLE_PRESETS = [
    ("None", "None"),
    ("Default", "Default"),
    ("Minimal", "Minimal"),
    ("BoldHeader", "Bold header"),
    ("AlternatingRows", "Alternating rows"),
    ("ContrastAlternatingRows", "Contrast alternating rows"),
    ("FlashyRows", "Flashy rows"),
    ("BoldHeaderFlashyRows", "Bold header flashy rows"),
    ("Sparse", "Sparse"),
    ("Condensed", "Condensed"),
    ("NumbersOnLeft", "Numbers on left"),
]


@dataclass
class CardSpec:
    """A named formatting card (e.g. background, title) and its properties."""

    key: str
    label: str
    props: List[PropSpec]


# -- Common cards, reused across visuals -------------------------------- #
_CARD_BACKGROUND = CardSpec(
    "background",
    "Background",
    [
        PropSpec("show", "Show", "bool", True),
        PropSpec("color", "Colour", "color", "#FFFFFF"),
        PropSpec("transparency", "Transparency %", "int", 0),
    ],
)
_CARD_BORDER = CardSpec(
    "border",
    "Border",
    [
        PropSpec("show", "Show", "bool", True),
        PropSpec("color", "Colour", "color", "#CCCCCC"),
        PropSpec("radius", "Radius", "int", 0),
    ],
)
_CARD_TITLE = CardSpec(
    "title",
    "Title",
    [
        PropSpec("show", "Show", "bool", True),
        PropSpec("fontColor", "Font colour", "color", "#FFFFFF"),
        PropSpec("background", "Background", "color", "#062B60"),
        PropSpec("alignment", "Alignment", "choice", "left", _ALIGNMENTS),
        PropSpec("fontSize", "Font size", "int", 12),
        PropSpec("fontFamily", "Font", "font", "Segoe UI"),
    ],
)
_CARD_LABELS = CardSpec(
    "labels",
    "Data labels",
    [
        PropSpec("color", "Colour", "color", "#000000"),
        PropSpec("labelDisplayUnits", "Display units", "choice", 0, _DISPLAY_UNITS),
        PropSpec("labelPrecision", "Decimal places", "int", 0),
        PropSpec("fontSize", "Font size", "int", 10),
        PropSpec("fontFamily", "Font", "font", "Segoe UI"),
    ],
)
_CARD_CATEGORY_LABELS = CardSpec(
    "categoryLabels",
    "Category labels",
    [
        PropSpec("show", "Show", "bool", True),
        PropSpec("color", "Colour", "color", "#01B8AA"),
        PropSpec("fontSize", "Font size", "int", 10),
        PropSpec("fontFamily", "Font", "font", "Segoe UI"),
    ],
)


def _schema(*cards: CardSpec) -> "OrderedDict[str, CardSpec]":
    return OrderedDict((c.key, c) for c in cards)


# The generic set of cards used for any visual without a specific schema.
CARD_SCHEMA: "OrderedDict[str, CardSpec]" = _schema(
    _CARD_BACKGROUND,
    _CARD_BORDER,
    _CARD_TITLE,
    _CARD_LABELS,
    _CARD_CATEGORY_LABELS,
)

# -- Table / matrix shared cards ---------------------------------------- #
_CARD_GRID = CardSpec(
    "grid",
    "Grid",
    [
        PropSpec("gridVertical", "Vertical gridlines", "bool", False),
        PropSpec("gridVerticalColor", "Vertical colour", "color", "#CCCCCC"),
        PropSpec("gridVerticalWeight", "Vertical thickness", "int", 1),
        PropSpec("gridHorizontal", "Horizontal gridlines", "bool", True),
        PropSpec("gridHorizontalColor", "Horizontal colour", "color", "#CCCCCC"),
        PropSpec("gridHorizontalWeight", "Horizontal thickness", "int", 1),
        PropSpec("rowPadding", "Row padding", "int", 2),
        PropSpec("outlineColor", "Outline colour", "color", "#CCCCCC"),
        PropSpec("outlineWeight", "Outline thickness", "int", 1),
        PropSpec("textSize", "Text size", "int", 10),
        PropSpec("imageHeight", "Image height", "int", 75),
    ],
)


def _values_card(extra: List[PropSpec]) -> CardSpec:
    props = [
        PropSpec("fontColorPrimary", "Font colour", "color", "#000000"),
        PropSpec("backColorPrimary", "Background", "color", "#FFFFFF"),
        PropSpec("fontColorSecondary", "Alt font colour", "color", "#000000"),
        PropSpec("backColorSecondary", "Alt background", "color", "#EEEEEE"),
    ]
    props += extra
    props += [
        PropSpec("urlIcon", "URL icon", "bool", False),
        PropSpec("wordWrap", "Word wrap", "bool", False),
        PropSpec("fontFamily", "Font", "font", "Segoe UI"),
        PropSpec("fontSize", "Font size", "int", 10),
    ]
    return CardSpec("values", "Values", props)


# -- Table (tableEx) ---------------------------------------------------- #
TABLE_CARD_SCHEMA = _schema(
    _CARD_BACKGROUND,
    _CARD_BORDER,
    _CARD_TITLE,
    _CARD_GRID,
    CardSpec(
        "columnHeaders",
        "Column headers",
        [
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("backColor", "Background", "color", "#FFFFFF"),
            PropSpec("autoSizeColumnWidth", "Auto-size width", "bool", True),
            PropSpec("alignment", "Alignment", "choice", "Left", _ALIGNMENTS_CAP),
            PropSpec("wordWrap", "Word wrap", "bool", False),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
            PropSpec("fontSize", "Font size", "int", 10),
        ],
    ),
    _values_card([]),
    CardSpec(
        "total",
        "Total",
        [
            PropSpec("totals", "Show totals", "bool", True),
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("backColor", "Background", "color", "#FFFFFF"),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
            PropSpec("fontSize", "Font size", "int", 10),
        ],
    ),
    CardSpec(
        "stylePreset",
        "Style preset",
        [PropSpec("name", "Preset", "choice", "Default", _TABLE_PRESETS)],
    ),
)

# -- Matrix (pivotTable) ------------------------------------------------ #
MATRIX_CARD_SCHEMA = _schema(
    _CARD_BACKGROUND,
    _CARD_BORDER,
    _CARD_TITLE,
    _CARD_GRID,
    CardSpec(
        "columnHeaders",
        "Column headers",
        [
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("backColor", "Background", "color", "#FFFFFF"),
            PropSpec("autoSizeColumnWidth", "Auto-size width", "bool", True),
            PropSpec("alignment", "Alignment", "choice", "Left", _ALIGNMENTS_CAP),
            PropSpec("titleAlignment", "Title alignment", "choice", "Auto", _TITLE_ALIGNMENTS),
            PropSpec("urlIcon", "URL icon", "bool", False),
            PropSpec("wordWrap", "Word wrap", "bool", False),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
            PropSpec("fontSize", "Font size", "int", 10),
        ],
    ),
    CardSpec(
        "rowHeaders",
        "Row headers",
        [
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("backColor", "Background", "color", "#FFFFFF"),
            PropSpec("stepped", "Stepped layout", "bool", True),
            PropSpec("steppedLayoutIndentation", "Indentation", "int", 10),
            PropSpec("showExpandCollapseButtons", "+/- buttons", "bool", True),
            PropSpec("urlIcon", "URL icon", "bool", False),
            PropSpec("wordWrap", "Word wrap", "bool", False),
            PropSpec("alignment", "Alignment", "choice", "Left", _ALIGNMENTS_CAP),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
            PropSpec("fontSize", "Font size", "int", 10),
        ],
    ),
    _values_card(
        [
            PropSpec("bandedRowHeaders", "Banded rows", "bool", False),
            PropSpec("valuesOnRow", "Values on rows", "bool", False),
        ]
    ),
    CardSpec(
        "subTotals",
        "Subtotals",
        [
            PropSpec("rowSubtotals", "Row subtotals", "bool", True),
            PropSpec("columnSubtotals", "Column subtotals", "bool", True),
            PropSpec("rowSubtotalsPosition", "Row position", "choice", "Bottom", _SUBTOTAL_POSITION),
            PropSpec("applyToHeaders", "Apply to headers", "bool", False),
            PropSpec("perRowLevel", "Per row level", "bool", False),
            PropSpec("perColumnLevel", "Per column level", "bool", False),
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("backColor", "Background", "color", "#FFFFFF"),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
            PropSpec("fontSize", "Font size", "int", 10),
        ],
    ),
    CardSpec(
        "total",
        "Grand total",
        [
            PropSpec("applyToHeaders", "Apply to headers", "bool", False),
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("backColor", "Background", "color", "#FFFFFF"),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
            PropSpec("fontSize", "Font size", "int", 10),
        ],
    ),
    CardSpec(
        "stylePreset",
        "Style preset",
        [PropSpec("name", "Preset", "choice", "Default", _TABLE_PRESETS)],
    ),
)

# -- Slicer ------------------------------------------------------------- #
SLICER_CARD_SCHEMA = _schema(
    _CARD_BACKGROUND,
    _CARD_BORDER,
    _CARD_TITLE,
    CardSpec(
        "general",
        "General",
        [
            PropSpec("orientation", "Orientation", "choice", 1, _ORIENTATION),
            PropSpec("outlineColor", "Outline colour", "color", "#444444"),
            PropSpec("outlineWeight", "Outline thickness", "int", 1),
        ],
    ),
    CardSpec(
        "header",
        "Header",
        [
            PropSpec("show", "Show", "bool", True),
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("background", "Background", "color", "#FFFFFF"),
            PropSpec("textSize", "Text size", "int", 10),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
        ],
    ),
    CardSpec(
        "items",
        "Items",
        [
            PropSpec("fontColor", "Font colour", "color", "#000000"),
            PropSpec("background", "Background", "color", "#FFFFFF"),
            PropSpec("textSize", "Text size", "int", 11),
            PropSpec("fontFamily", "Font", "font", "Segoe UI"),
        ],
    ),
    CardSpec(
        "selection",
        "Selection controls",
        [
            PropSpec("selectAllCheckboxEnabled", "Show 'Select all'", "bool", False),
            PropSpec("singleSelect", "Single select", "bool", True),
        ],
    ),
    CardSpec(
        "slider",
        "Slider",
        [PropSpec("color", "Colour", "color", "#118DFF")],
    ),
)

# Visuals with a dedicated, detailed card schema; others use CARD_SCHEMA.
VISUAL_CARD_SCHEMA: "OrderedDict[str, OrderedDict[str, CardSpec]]" = OrderedDict(
    [
        ("tableEx", TABLE_CARD_SCHEMA),
        ("pivotTable", MATRIX_CARD_SCHEMA),
        ("slicer", SLICER_CARD_SCHEMA),
    ]
)


def cards_for(visual: str) -> "OrderedDict[str, CardSpec]":
    """Return the card schema for *visual* (specific if defined, else generic)."""
    return VISUAL_CARD_SCHEMA.get(visual, CARD_SCHEMA)


# Friendly names for the visuals a style can target.  "*" means "all visuals".
# This covers every visual defined by the Power BI report theme schema
# (v2.157), ordered by category for usability.
VISUAL_TARGETS: "OrderedDict[str, str]" = OrderedDict(
    [
        ("*", "All visuals (*)"),
        # Cards & KPIs
        ("card", "Card"),
        ("cardVisual", "Card (new)"),
        ("multiRowCard", "Multi-row card"),
        ("kpi", "KPI"),
        ("gauge", "Gauge"),
        ("scorecard", "Scorecard (goals)"),
        # Column / bar charts
        ("columnChart", "Stacked column"),
        ("clusteredColumnChart", "Clustered column"),
        ("hundredPercentStackedColumnChart", "100% stacked column"),
        ("barChart", "Stacked bar"),
        ("clusteredBarChart", "Clustered bar"),
        ("hundredPercentStackedBarChart", "100% stacked bar"),
        ("ribbonChart", "Ribbon chart"),
        ("waterfallChart", "Waterfall"),
        ("funnel", "Funnel"),
        # Line / area / combo charts
        ("lineChart", "Line chart"),
        ("areaChart", "Area chart"),
        ("stackedAreaChart", "Stacked area"),
        ("hundredPercentStackedAreaChart", "100% stacked area"),
        ("lineClusteredColumnComboChart", "Line & clustered column"),
        ("lineStackedColumnComboChart", "Line & stacked column"),
        # Part-to-whole / distribution
        ("pieChart", "Pie chart"),
        ("donutChart", "Donut chart"),
        ("treemap", "Treemap"),
        ("scatterChart", "Scatter chart"),
        # Tables
        ("tableEx", "Table"),
        ("pivotTable", "Matrix"),
        # Maps
        ("map", "Map"),
        ("filledMap", "Filled map"),
        ("shapeMap", "Shape map"),
        ("azureMap", "Azure map"),
        # Slicers & filters
        ("slicer", "Slicer"),
        ("advancedSlicerVisual", "Slicer (new)"),
        ("listSlicer", "List slicer"),
        ("textSlicer", "Text slicer"),
        ("filter", "Filter"),
        # AI & analytics
        ("keyDriversVisual", "Key influencers"),
        ("decompositionTreeVisual", "Decomposition tree"),
        ("aiNarratives", "Smart narrative"),
        ("qnaVisual", "Q&A"),
        # Script visuals
        ("pythonVisual", "Python visual"),
        ("scriptVisual", "R visual"),
        ("rdlVisual", "Paginated report (RDL)"),
        # Elements & navigation
        ("actionButton", "Button"),
        ("textbox", "Text box"),
        ("image", "Image"),
        ("shape", "Shape"),
        ("pageNavigator", "Page navigator"),
        ("bookmarkNavigator", "Bookmark navigator"),
        ("group", "Group"),
        # Page & report level
        ("page", "Page"),
        ("report", "Report"),
    ]
)


class VisualStyle:
    """Formatting for one visual target (``visualStyles[visual]["*"]``).

    Holds, per card, whether it is enabled and the editor values for its
    properties.  Only enabled cards are emitted.
    """

    def __init__(self, visual: str = "*") -> None:
        self.visual = visual
        schema = cards_for(visual)
        self.enabled: Dict[str, bool] = {key: False for key in schema}
        self.values: Dict[str, Dict[str, Any]] = {
            key: {p.key: p.default for p in spec.props}
            for key, spec in schema.items()
        }

    @property
    def schema(self) -> "OrderedDict[str, CardSpec]":
        return cards_for(self.visual)

    def to_dict(self) -> Dict[str, Any]:
        """Return ``{card: [ {props...} ]}`` for the enabled cards only."""
        cards: Dict[str, Any] = OrderedDict()
        for key, spec in self.schema.items():
            if not self.enabled.get(key):
                continue
            obj: Dict[str, Any] = OrderedDict()
            for prop in spec.props:
                value = self.values[key].get(prop.key, prop.default)
                obj[prop.key] = prop.to_json_value(value)
            cards[key] = [obj]
        return cards

    @classmethod
    def from_dict(cls, visual: str, cards: Dict[str, Any]) -> "VisualStyle":
        style = cls(visual)
        for key, spec in style.schema.items():
            if key not in cards:
                continue
            entries = cards[key]
            obj = entries[0] if isinstance(entries, list) and entries else {}
            if not isinstance(obj, dict):
                continue
            style.enabled[key] = True
            for prop in spec.props:
                if prop.key in obj:
                    style.values[key][prop.key] = prop.from_json_value(obj[prop.key])
        return style


# --------------------------------------------------------------------------- #
# The theme itself
# --------------------------------------------------------------------------- #
class PowerBITheme:
    """In-memory representation of a Power BI report theme."""

    #: Structural colour fields -> (attr, JSON key, human label, default value).
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
        # Start with a single, empty "all visuals" target.
        self.visual_styles: List[VisualStyle] = [VisualStyle("*")]

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Build the JSON-ready dict, omitting empty/optional values."""
        theme: Dict[str, Any] = OrderedDict()
        theme["name"] = self.name or "My Theme"

        colors = [normalise_hex(c) for c in self.data_colors if is_valid_hex(c)]
        if colors:
            theme["dataColors"] = colors

        for attr, key, _label, _default in self.STRUCTURAL_FIELDS:
            value = getattr(self, attr)
            if is_valid_hex(value):
                theme[key] = normalise_hex(value)

        text_classes = OrderedDict(
            (name, tc.to_dict())
            for name, tc in self.text_classes.items()
            if tc.to_dict()
        )
        if text_classes:
            theme["textClasses"] = text_classes

        visual_styles: Dict[str, Any] = OrderedDict()
        for style in self.visual_styles:
            cards = style.to_dict()
            if cards:
                visual_styles[style.visual] = {"*": cards}
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

        for attr, key, _label, _default in cls.STRUCTURAL_FIELDS:
            if key in data:
                setattr(theme, attr, str(data[key]))

        raw_classes = data.get("textClasses")
        if isinstance(raw_classes, dict):
            theme.text_classes = OrderedDict(
                (name, TextClass.from_dict(name, value))
                for name, value in raw_classes.items()
                if isinstance(value, dict)
            )

        raw_visuals = data.get("visualStyles")
        if isinstance(raw_visuals, dict) and raw_visuals:
            styles: List[VisualStyle] = []
            for visual, selectors in raw_visuals.items():
                cards = {}
                if isinstance(selectors, dict):
                    cards = selectors.get("*", {})
                styles.append(VisualStyle.from_dict(visual, cards or {}))
            if styles:
                theme.visual_styles = styles

        return theme

    @classmethod
    def load(cls, path: str) -> "PowerBITheme":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
