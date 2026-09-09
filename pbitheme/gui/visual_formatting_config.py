"""Visual formatting configuration mapping visual types to their styling options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Field types for formatting options
FieldType = Literal["color", "boolean", "number", "dropdown", "text"]


@dataclass
class FormatField:
    """A single formatting field for a visual."""

    key: str  # JSON key name
    label: str  # UI label
    field_type: FieldType
    default: str | bool | int | None = None
    options: list[tuple[str, str]] | None = None  # For dropdowns: (value, label)
    min_val: int | None = None  # For numbers
    max_val: int | None = None
    suffix: str | None = None  # For numbers: "px", "%", "pt"
    preview: bool = True  # False = exported to the theme but not shown in the live preview


@dataclass
class FormatSection:
    """A section of formatting options (e.g., "Gridlines", "Row Headers")."""

    name: str
    fields: list[FormatField]


# Common font families offered by dropdowns (export-only where used).
FONT_OPTIONS = [
    ("Segoe UI", "Segoe UI"), ("Segoe UI Semibold", "Segoe UI Semibold"),
    ("Arial", "Arial"), ("Calibri", "Calibri"), ("Tahoma", "Tahoma"),
    ("Verdana", "Verdana"), ("Georgia", "Georgia"), ("Times New Roman", "Times New Roman"),
    ("Trebuchet MS", "Trebuchet MS"), ("Courier New", "Courier New"), ("DIN", "DIN"),
]

# Matrix and Table formatting sections
MATRIX_TABLE_SECTIONS = [
    FormatSection(
        "Gridlines",
        [
            FormatField("gridlineStyle", "Gridline Style", "dropdown",
                       options=[("None", "None"), ("Solid", "Solid"), ("Dashed", "Dashed")]),
            FormatField("gridlineColor", "Gridline Color", "color", default="#CCCCCC"),
            FormatField("gridlineThickness", "Gridline Thickness (px)", "number", min_val=1, max_val=5, suffix="px"),
            FormatField("rowSpacing", "Row Spacing (px)", "number", min_val=0, max_val=20, suffix="px"),
            FormatField("gridOutlineColor", "Outline Color", "color", default="#CCCCCC"),
            FormatField("gridOutlineWeight", "Outline Weight (px)", "number", min_val=0, max_val=5, default=1, suffix="px"),
            FormatField("gridTextSize", "Overall Text Size (pt)", "number", min_val=8, max_val=28, default=10, suffix="pt", preview=False),
        ],
    ),
    FormatSection(
        "Row Headers",
        [
            FormatField("rowHeaderBackgroundColor", "Background Color", "color", default="#F5F5F5"),
            FormatField("rowHeaderTextColor", "Text Color", "color", default="#252423"),
            FormatField("rowHeaderFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("rowHeaderFontBold", "Bold", "boolean", default=False),
            FormatField("rowHeaderItalic", "Italic", "boolean", default=False),
            FormatField("rowHeaderUnderline", "Underline", "boolean", default=False),
            FormatField("rowHeaderAlignment", "Alignment", "dropdown",
                       options=[("Left", "Left"), ("Center", "Center"), ("Right", "Right")]),
            FormatField("rowHeaderStepped", "Stepped Layout", "boolean", default=True),
            FormatField("rowHeaderFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
    FormatSection(
        "Column Headers",
        [
            FormatField("columnHeaderBackgroundColor", "Background Color", "color", default="#F5F5F5"),
            FormatField("columnHeaderTextColor", "Text Color", "color", default="#252423"),
            FormatField("columnHeaderFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("columnHeaderFontBold", "Bold", "boolean", default=False),
            FormatField("columnHeaderItalic", "Italic", "boolean", default=False),
            FormatField("columnHeaderUnderline", "Underline", "boolean", default=False),
            FormatField("columnHeaderAlignment", "Alignment", "dropdown",
                       options=[("Left", "Left"), ("Center", "Center"), ("Right", "Right")]),
            FormatField("columnHeaderFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("columnHeaderWordWrap", "Word Wrap", "boolean", default=False, preview=False),
        ],
    ),
    FormatSection(
        "Values",
        [
            FormatField("valuesBackgroundColor", "Background Color", "color", default="#FFFFFF"),
            FormatField("valuesTextColor", "Text Color", "color", default="#252423"),
            FormatField("valuesFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("valuesFontBold", "Bold", "boolean", default=False),
            FormatField("valuesItalic", "Italic", "boolean", default=False),
            FormatField("valuesUnderline", "Underline", "boolean", default=False),
            FormatField("valuesAlignment", "Alignment", "dropdown",
                       options=[("Left", "Left"), ("Center", "Center"), ("Right", "Right")]),
            FormatField("cellPadding", "Cell Padding (px)", "number", min_val=2, max_val=20, suffix="px"),
            FormatField("bandedRows", "Banded Rows", "boolean", default=False),
            FormatField("alternateRowColor", "Alternate Row Color", "color", default="#F5F5F5"),
            FormatField("valuesFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("valuesWordWrap", "Word Wrap", "boolean", default=False, preview=False),
        ],
    ),
    FormatSection(
        "Totals",
        [
            FormatField("showTotals", "Show Totals", "boolean", default=True),
            FormatField("totalsBackgroundColor", "Background Color", "color", default="#E8E8E8"),
            FormatField("totalsTextColor", "Text Color", "color", default="#000000"),
            FormatField("totalsFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, default=12, suffix="pt"),
            FormatField("totalsFontBold", "Bold", "boolean", default=True),
            FormatField("totalsItalic", "Italic", "boolean", default=False),
            FormatField("totalsUnderline", "Underline", "boolean", default=False),
            FormatField("totalsFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("totalsLabel", "Label (Table)", "text", default="", preview=False),
            FormatField("totalsApplyToHeaders", "Apply to Headers (Matrix)", "boolean", default=False, preview=False),
        ],
    ),
    FormatSection(
        "Subtotals",
        [
            FormatField("showSubtotals", "Show Subtotals", "boolean", default=True),
            FormatField("subtotalsBackgroundColor", "Background Color", "color", default="#F0F0F0"),
            FormatField("subtotalsTextColor", "Text Color", "color", default="#252423"),
            FormatField("subtotalsFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, default=11, suffix="pt"),
            FormatField("subtotalsFontBold", "Bold", "boolean", default=True),
            FormatField("subtotalsItalic", "Italic", "boolean", default=False),
            FormatField("subtotalsUnderline", "Underline", "boolean", default=False),
            FormatField("columnSubtotals", "Show Column Subtotals", "boolean", default=True, preview=False),
            FormatField("subtotalsFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
    FormatSection(
        "Data Bars",
        [
            FormatField("dataBarsShow", "Show Data Bars", "boolean", default=False),
            FormatField("dataBarsPositiveColor", "Positive Color", "color", default="#118DFF"),
            FormatField("dataBarsNegativeColor", "Negative Color", "color", default="#D64550", preview=False),
            FormatField("dataBarsAxisColor", "Axis Color", "color", default="#808080", preview=False),
            FormatField("dataBarsHideText", "Bars Only (Hide Text)", "boolean", default=False, preview=False),
            FormatField("dataBarsReverse", "Reverse Direction", "boolean", default=False, preview=False),
        ],
    ),
    FormatSection(
        "Column Sizing",
        [
            FormatField("columnAutoSize", "Auto-Size Width", "boolean", default=True, preview=False),
            FormatField("defaultColumnWidth", "Default Width (px)", "number", min_val=20, max_val=400, default=120, suffix="px", preview=False),
        ],
    ),
    FormatSection(
        "Blank Rows",  # matrix only on export
        [
            FormatField("blankRowsShow", "Show Blank Rows", "boolean", default=False, preview=False),
            FormatField("blankRowColor", "Fill Color", "color", default="#F5F5F5", preview=False),
            FormatField("blankRowBorderColor", "Border Color", "color", default="#CCCCCC", preview=False),
        ],
    ),
    FormatSection(
        "Sparklines",
        [
            FormatField("sparklineType", "Chart Type", "dropdown",
                       options=[("line", "Line"), ("column", "Column")], preview=False),
            FormatField("sparklineColor", "Line/Bar Color", "color", default="#118DFF", preview=False),
            FormatField("sparklineMarkerColor", "Marker Color", "color", default="#E66C37", preview=False),
        ],
    ),
    FormatSection(
        "Table Style",
        [
            FormatField("stylePreset", "Built-in Style", "dropdown",
                       options=[("None", "None"), ("Minimal", "Minimal"), ("BoldHeader", "Bold header"),
                                ("AlternatingRows", "Alternating rows"),
                                ("ContrastAlternatingRows", "Contrast alternating rows"),
                                ("FlashyRows", "Flashy rows"),
                                ("BoldHeaderFlashyRows", "Bold header flashy rows"),
                                ("Sparse", "Sparse"), ("Condensed", "Condensed")],
                       preview=False),
        ],
    ),
]

# Chart formatting sections
CHART_SECTIONS = [
    FormatSection(
        "X-Axis",
        [
            FormatField("xAxisTitleText", "Title Text", "text", default=""),
            FormatField("xAxisLabelColor", "Label Color", "color", default="#252423"),
            FormatField("xAxisLabelFontSize", "Font Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
            FormatField("xAxisBold", "Bold", "boolean", default=False),
            FormatField("xAxisItalic", "Italic", "boolean", default=False),
            FormatField("xAxisFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("xAxisTitleColor", "Title Color", "color", default="#252423"),
            FormatField("xAxisTitleFontSize", "Title Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
        ],
    ),
    FormatSection(
        "Y-Axis",
        [
            FormatField("yAxisTitleText", "Title Text", "text", default=""),
            FormatField("yAxisLogScale", "Log Scale", "boolean", default=False),
            FormatField("yAxisSetRange", "Fixed Range", "boolean", default=False),
            FormatField("yAxisStart", "Range Start", "number", min_val=0, max_val=100000, default=0),
            FormatField("yAxisEnd", "Range End", "number", min_val=1, max_val=100000, default=100),
            FormatField("yAxisLabelColor", "Label Color", "color", default="#252423"),
            FormatField("yAxisLabelFontSize", "Font Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
            FormatField("yAxisBold", "Bold", "boolean", default=False),
            FormatField("yAxisItalic", "Italic", "boolean", default=False),
            FormatField("yAxisFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("yAxisDisplayUnits", "Display Units", "dropdown",
                       options=[("1", "None"), ("1000", "Thousands"), ("1000000", "Millions"),
                                ("1000000000", "Billions")], preview=False),
            FormatField("yAxisPrecision", "Decimal Places", "number", min_val=0, max_val=4, preview=False),
            FormatField("yAxisTitleColor", "Title Color", "color", default="#252423"),
            FormatField("yAxisTitleFontSize", "Title Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
        ],
    ),
    FormatSection(
        "Gridlines",
        [
            FormatField("gridlineStyle", "Style", "dropdown",
                       options=[("None", "None"), ("Solid", "Solid"), ("Dashed", "Dashed")]),
            FormatField("gridlineColor", "Color", "color", default="#CCCCCC"),
            FormatField("gridlineThickness", "Thickness (px)", "number", min_val=1, max_val=3, suffix="px"),
        ],
    ),
    FormatSection(
        "Data Labels",
        [
            FormatField("dataLabelColor", "Color", "color", default="#252423"),
            FormatField("dataLabelFontSize", "Font Size (pt)", "number", min_val=8, max_val=16, suffix="pt"),
            FormatField("dataLabelBold", "Bold", "boolean", default=False),
            FormatField("dataLabelItalic", "Italic", "boolean", default=False),
            FormatField("dataLabelFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("dataLabelBackground", "Show Background", "boolean", default=False),
            FormatField("dataLabelDisplayUnits", "Display Units", "dropdown",
                       options=[("1", "None"), ("1000", "Thousands"), ("1000000", "Millions"),
                                ("1000000000", "Billions")]),
            FormatField("dataLabelPrecision", "Decimal Places", "number", min_val=0, max_val=4),
            FormatField("dataLabelPosition", "Position", "dropdown",
                       options=[("Auto", "Auto"), ("OutsideEnd", "Outside End"), ("InsideEnd", "Inside End"),
                                ("InsideCenter", "Inside Center"), ("InsideBase", "Inside Base")]),
        ],
    ),
    FormatSection(
        "Legend",
        [
            FormatField("legendPosition", "Position", "dropdown",
                       options=[("Top", "Top"), ("Bottom", "Bottom"), ("Left", "Left"), ("Right", "Right")]),
            FormatField("legendTextColor", "Text Color", "color", default="#252423"),
            FormatField("legendFontSize", "Font Size (pt)", "number", min_val=8, max_val=16, suffix="pt"),
            FormatField("legendBold", "Bold", "boolean", default=False),
            FormatField("legendItalic", "Italic", "boolean", default=False),
            FormatField("legendFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("legendShowTitle", "Show Title", "boolean", default=False),
            FormatField("legendTitleText", "Title Text", "text", default=""),
        ],
    ),
    FormatSection(
        "Data Colors",
        [
            FormatField("defaultColor", "Default Color", "color", default="#118DFF"),
        ],
    ),
    FormatSection(
        "Reference Line",
        [
            FormatField("refLineShow", "Show", "boolean", default=False),
            FormatField("refLineValue", "Value", "number", min_val=0, max_val=100, default=50),
            FormatField("refLineColor", "Color", "color", default="#E66C37"),
        ],
    ),
    FormatSection(
        "Trend Line",
        [
            FormatField("trendShow", "Show", "boolean", default=False),
            FormatField("trendColor", "Color", "color", default="#605E5C"),
        ],
    ),
    FormatSection(
        "Plot Area",
        [
            FormatField("plotAreaTransparency", "Transparency (%)", "number", min_val=0, max_val=100, default=0, suffix="%", preview=False),
        ],
    ),
]

# Small multiples layout -- supported by cartesian charts (not scatter/waterfall).
SMALL_MULTIPLES_SECTION = FormatSection(
    "Small Multiples",
    [
        FormatField("smColumnCount", "Columns", "number", min_val=1, max_val=10, default=2, preview=False),
        FormatField("smRowCount", "Rows", "number", min_val=1, max_val=10, default=2, preview=False),
        FormatField("smGridlineColor", "Gridline Color", "color", default="#E1E1E1", preview=False),
        FormatField("smBackgroundColor", "Background Color", "color", default="#FFFFFF", preview=False),
    ],
)

# Cartesian charts that additionally expose the small-multiples layout card.
CHART_SECTIONS_SM = CHART_SECTIONS + [SMALL_MULTIPLES_SECTION]

# Scatter = chart sections plus marker / bubble options + a ratio line.
SCATTER_SECTIONS = CHART_SECTIONS + [
    FormatSection(
        "Markers",
        [
            FormatField("bubbleSize", "Bubble Size", "number", min_val=0, max_val=100, default=20),
            FormatField("markerBorderColor", "Border Color", "color", default="#FFFFFF"),
        ],
    ),
    FormatSection(
        "Ratio Line",
        [
            FormatField("ratioLineShow", "Show", "boolean", default=False),
            FormatField("ratioLineColor", "Color", "color", default="#605E5C"),
        ],
    ),
]

# Waterfall = chart sections plus sentiment (increase / decrease / total) colours.
# The shared "Default Color" acts as the increase colour.
WATERFALL_SECTIONS = CHART_SECTIONS + [
    FormatSection(
        "Sentiment Colors",
        [
            FormatField("decreaseColor", "Decrease Color", "color", default="#D64550"),
            FormatField("totalColor", "Total Color", "color", default="#118DFF"),
        ],
    ),
]

# Card and KPI formatting
CARD_KPI_SECTIONS = [
    FormatSection(
        "Value",
        [
            FormatField("valueColor", "Color", "color", default="#000000"),
            FormatField("valueFontSize", "Font Size (pt)", "number", min_val=12, max_val=72, suffix="pt"),
            FormatField("valueFontBold", "Bold", "boolean", default=True),
        ],
    ),
    FormatSection(
        "Label",
        [
            FormatField("labelColor", "Color", "color", default="#252423"),
            FormatField("labelFontSize", "Font Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
        ],
    ),
    FormatSection(
        "Background",
        [
            FormatField("backgroundColor", "Color", "color", default="#FFFFFF"),
            FormatField("backgroundBorder", "Show Border", "boolean", default=False),
        ],
    ),
]

# Pie / Donut -- no cartesian axes or gridlines; legend + slice data labels.
PIE_SECTIONS = [
    FormatSection(
        "Legend",
        [
            FormatField("legendPosition", "Position", "dropdown",
                       options=[("Top", "Top"), ("Bottom", "Bottom"), ("Left", "Left"), ("Right", "Right")]),
            FormatField("legendTextColor", "Text Color", "color", default="#252423"),
            FormatField("legendFontSize", "Font Size (pt)", "number", min_val=8, max_val=16, suffix="pt"),
            FormatField("legendBold", "Bold", "boolean", default=False),
            FormatField("legendItalic", "Italic", "boolean", default=False),
            FormatField("legendFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
    FormatSection(
        "Data Labels",
        [
            FormatField("showDataLabels", "Show Labels", "boolean", default=True),
            FormatField("dataLabelColor", "Color", "color", default="#FFFFFF"),
            FormatField("dataLabelFontSize", "Font Size (pt)", "number", min_val=6, max_val=16, suffix="pt"),
            FormatField("dataLabelBold", "Bold", "boolean", default=False),
            FormatField("dataLabelItalic", "Italic", "boolean", default=False),
            FormatField("dataLabelFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
    FormatSection(
        "Slices",
        [
            FormatField("sliceStartAngle", "Start Angle (deg)", "number", min_val=0, max_val=359, default=0),
            FormatField("sliceInnerRadius", "Inner Radius (%)", "number", min_val=0, max_val=90, default=0),
        ],
    ),
]

# Gauge -- radial: min/max scale, fill & target colours, callout value.
GAUGE_SECTIONS = [
    FormatSection(
        "Axis",
        [
            FormatField("minValue", "Minimum", "number", min_val=0, max_val=1000, default=0),
            FormatField("maxValue", "Maximum", "number", min_val=1, max_val=1000, default=100),
            FormatField("targetValue", "Target", "number", min_val=0, max_val=1000, default=85),
        ],
    ),
    FormatSection(
        "Colors",
        [
            FormatField("fillColor", "Fill Color", "color", default="#118DFF"),
            FormatField("targetColor", "Target Color", "color", default="#E66C37"),
        ],
    ),
    FormatSection(
        "Callout Value",
        [
            FormatField("showCallout", "Show Value", "boolean", default=True),
            FormatField("calloutColor", "Color", "color", default="#252423"),
            FormatField("calloutFontSize", "Font Size (pt)", "number", min_val=10, max_val=48, suffix="pt"),
        ],
    ),
]

# Treemap -- coloured rectangles; legend + category/value labels.
TREEMAP_SECTIONS = [
    FormatSection(
        "Legend",
        [
            FormatField("legendPosition", "Position", "dropdown",
                       options=[("Top", "Top"), ("Bottom", "Bottom"), ("Left", "Left"), ("Right", "Right")]),
            FormatField("legendTextColor", "Text Color", "color", default="#252423"),
            FormatField("legendFontSize", "Font Size (pt)", "number", min_val=8, max_val=16, suffix="pt"),
            FormatField("legendBold", "Bold", "boolean", default=False),
            FormatField("legendItalic", "Italic", "boolean", default=False),
            FormatField("legendFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
    FormatSection(
        "Data Labels",
        [
            FormatField("showDataLabels", "Show Labels", "boolean", default=True),
            FormatField("dataLabelColor", "Color", "color", default="#FFFFFF"),
            FormatField("dataLabelFontSize", "Font Size (pt)", "number", min_val=6, max_val=16, suffix="pt"),
            FormatField("dataLabelBold", "Bold", "boolean", default=False),
            FormatField("dataLabelItalic", "Italic", "boolean", default=False),
            FormatField("dataLabelFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
]

# Funnel -- decreasing stages; bar colour + data labels (no legend card).
FUNNEL_SECTIONS = [
    FormatSection(
        "Bars",
        [
            FormatField("barColor", "Bar Color", "color", default="#118DFF"),
        ],
    ),
    FormatSection(
        "Data Labels",
        [
            FormatField("showDataLabels", "Show Labels", "boolean", default=True),
            FormatField("dataLabelColor", "Color", "color", default="#FFFFFF"),
            FormatField("dataLabelFontSize", "Font Size (pt)", "number", min_val=6, max_val=16, suffix="pt"),
            FormatField("dataLabelBold", "Bold", "boolean", default=False),
            FormatField("dataLabelItalic", "Italic", "boolean", default=False),
            FormatField("dataLabelFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
]

_ICON_SHAPES = [
    ("blank", "Blank"), ("leftArrow", "Left arrow"), ("rightArrow", "Right arrow"),
    ("back", "Back"), ("reset", "Reset"), ("help", "Help"), ("information", "Information"),
    ("qna", "Q&A"), ("bookmarks", "Bookmark"),
]

# Action button -- fill / text / outline (default state) + icon, glow, shadow, hover.
ACTION_BUTTON_SECTIONS = [
    FormatSection(
        "Button",
        [
            FormatField("buttonFillColor", "Fill Color", "color", default="#118DFF"),
            FormatField("buttonTextColor", "Text Color", "color", default="#FFFFFF"),
            FormatField("buttonOutlineColor", "Outline Color", "color", default="#118DFF"),
            FormatField("buttonOutlineWeight", "Outline Weight (px)", "number", min_val=0, max_val=10, default=0, preview=False),
        ],
    ),
    FormatSection(
        "Icon",
        [
            FormatField("buttonIconShape", "Shape", "dropdown", options=_ICON_SHAPES, preview=False),
            FormatField("buttonIconColor", "Line Color", "color", default="#FFFFFF", preview=False),
            FormatField("buttonIconSize", "Size (pt)", "number", min_val=8, max_val=60, default=16, suffix="pt", preview=False),
        ],
    ),
    FormatSection(
        "Hover State",
        [
            FormatField("buttonHoverFillColor", "Fill Color", "color", default="#0B6BC2", preview=False),
            FormatField("buttonHoverTextColor", "Text Color", "color", default="#FFFFFF", preview=False),
        ],
    ),
    FormatSection(
        "Glow & Shadow",
        [
            FormatField("buttonGlowShow", "Show Glow", "boolean", default=False, preview=False),
            FormatField("buttonGlowColor", "Glow Color", "color", default="#118DFF", preview=False),
            FormatField("buttonShadowShow", "Show Shadow", "boolean", default=False, preview=False),
            FormatField("buttonShadowColor", "Shadow Color", "color", default="#000000", preview=False),
        ],
    ),
]

# Basic shape -- fill + outline.
SHAPE_SECTIONS = [
    FormatSection(
        "Shape",
        [
            FormatField("shapeFillColor", "Fill Color", "color", default="#118DFF"),
            FormatField("shapeOutlineColor", "Outline Color", "color", default="#000000"),
            FormatField("shapeOutlineWeight", "Outline Weight (px)", "number", min_val=0, max_val=10, default=1, preview=False),
        ],
    ),
]

# Decomposition tree -- level headers + data labels.
DECOMP_SECTIONS = [
    FormatSection(
        "Level Header",
        [
            FormatField("levelHeaderBg", "Background Color", "color", default="#118DFF"),
            FormatField("levelTitleColor", "Title Color", "color", default="#FFFFFF"),
        ],
    ),
    FormatSection(
        "Data Labels",
        [
            FormatField("treeDataLabelColor", "Color", "color", default="#252423", preview=False),
        ],
    ),
]

_MAP_THEMES = [
    ("road", "Road"), ("aerial", "Aerial"), ("grayscale", "Grayscale"),
    ("canvasLight", "Light"), ("canvasDark", "Dark"),
]

# Map style + controls, shared by the base map and the filled map.
_MAP_STYLE_SECTIONS = [
    FormatSection(
        "Map Style",
        [
            FormatField("mapTheme", "Theme", "dropdown", options=_MAP_THEMES, preview=False),
            FormatField("mapShowLabels", "Show Labels", "boolean", default=True, preview=False),
        ],
    ),
    FormatSection(
        "Controls",
        [
            FormatField("mapAutoZoom", "Auto Zoom", "boolean", default=True, preview=False),
            FormatField("mapShowZoom", "Zoom Buttons", "boolean", default=True, preview=False),
        ],
    ),
]

# Map / Filled map -- data point colour + category labels.
MAP_SECTIONS = [
    FormatSection(
        "Data Colors",
        [
            FormatField("mapDataColor", "Data Point Color", "color", default="#118DFF"),
        ],
    ),
    FormatSection(
        "Category Labels",
        [
            FormatField("mapLabelColor", "Label Color", "color", default="#252423", preview=False),
        ],
    ),
] + _MAP_STYLE_SECTIONS

FILLED_MAP_SECTIONS = [
    FormatSection(
        "Data Colors",
        [
            FormatField("mapDataColor", "Region Color", "color", default="#118DFF"),
            FormatField("mapStrokeColor", "Border Color", "color", default="#FFFFFF"),
        ],
    ),
] + _MAP_STYLE_SECTIONS

# Shape map -- default fill + border.
SHAPE_MAP_SECTIONS = [
    FormatSection(
        "Shapes",
        [
            FormatField("shapeMapColor", "Default Color", "color", default="#118DFF"),
            FormatField("shapeMapBorderColor", "Border Color", "color", default="#FFFFFF"),
        ],
    ),
]

# Image -- scaling mode (export-only).
IMAGE_SECTIONS = [
    FormatSection(
        "Image",
        [
            FormatField("imageScaling", "Scaling", "dropdown",
                       options=[("Normal", "Fit"), ("Fit", "Stretch"), ("Fill", "Fill")], preview=False),
        ],
    ),
]

# Text box -- text colour / size / font.
TEXTBOX_SECTIONS = [
    FormatSection(
        "Text",
        [
            FormatField("textColor", "Color", "color", default="#252423"),
            FormatField("textFontSize", "Font Size (pt)", "number", min_val=8, max_val=60, default=14, suffix="pt"),
            FormatField("textFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
        ],
    ),
]

# Smart narrative (aiNarratives) -- generated-text colour / size / font / alignment.
SMART_NARRATIVE_SECTIONS = [
    FormatSection(
        "Text",
        [
            FormatField("narrativeTextColor", "Color", "color", default="#252423"),
            FormatField("narrativeFontSize", "Font Size (pt)", "number", min_val=8, max_val=60, default=12, suffix="pt"),
            FormatField("narrativeFontFamily", "Font Family", "dropdown", options=FONT_OPTIONS, preview=False),
            FormatField("narrativeAlignment", "Alignment", "dropdown",
                       options=[("Auto", "Auto"), ("Left", "Left"), ("Center", "Center"), ("Right", "Right")],
                       preview=False),
        ],
    ),
]

# KPI -- indicator value, goal, trend line and status colours.
KPI_SECTIONS = [
    FormatSection(
        "Indicator",
        [
            FormatField("indicatorFontColor", "Color", "color", default="#252423"),
            FormatField("indicatorFontSize", "Font Size (pt)", "number", min_val=12, max_val=60, suffix="pt"),
            FormatField("indicatorBold", "Bold", "boolean", default=True),
        ],
    ),
    FormatSection(
        "Goal",
        [
            FormatField("showGoal", "Show Goal", "boolean", default=True),
            FormatField("goalFontColor", "Color", "color", default="#605E5C"),
            FormatField("goalFontSize", "Font Size (pt)", "number", min_val=8, max_val=40, suffix="pt"),
        ],
    ),
    FormatSection(
        "Trend & Status",
        [
            FormatField("trendlineShow", "Show Trend Line", "boolean", default=True),
            FormatField("statusGoodColor", "Good Color", "color", default="#1AAB40"),
            FormatField("statusBadColor", "Bad Color", "color", default="#D64550"),
        ],
    ),
]

# Slicer -- header + selectable items.
SLICER_SECTIONS = [
    FormatSection(
        "Header",
        [
            FormatField("headerShow", "Show Header", "boolean", default=True),
            FormatField("headerFontColor", "Font Color", "color", default="#252423"),
            FormatField("headerBackground", "Background", "color", default="#FFFFFF"),
            FormatField("headerTextSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("headerBold", "Bold", "boolean", default=False),
        ],
    ),
    FormatSection(
        "Items",
        [
            FormatField("itemsFontColor", "Font Color", "color", default="#252423"),
            FormatField("itemsBackground", "Background", "color", default="#FFFFFF"),
            FormatField("itemsTextSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("itemsBold", "Bold", "boolean", default=False),
        ],
    ),
    FormatSection(
        "Selection",
        [
            FormatField("selectionColor", "Checkbox Color", "color", default="#118DFF"),
        ],
    ),
    FormatSection(
        "Slider",
        [
            FormatField("sliderColor", "Slider Color", "color", default="#118DFF", preview=False),
        ],
    ),
    FormatSection(
        "Search Box",
        [
            FormatField("searchBackground", "Background", "color", default="#FFFFFF", preview=False),
            FormatField("searchBorderColor", "Border Color", "color", default="#C8C6C4", preview=False),
        ],
    ),
    FormatSection(
        "Date Slicer",
        [
            FormatField("dateFontColor", "Font Color", "color", default="#252423", preview=False),
            FormatField("dateBackground", "Background", "color", default="#FFFFFF", preview=False),
            FormatField("dateTextSize", "Font Size (pt)", "number", min_val=8, max_val=28, default=11, suffix="pt", preview=False),
        ],
    ),
    FormatSection(
        "Numeric Slicer",
        [
            FormatField("numericFontColor", "Font Color", "color", default="#252423", preview=False),
            FormatField("numericBackground", "Background", "color", default="#FFFFFF", preview=False),
            FormatField("numericTextSize", "Font Size (pt)", "number", min_val=8, max_val=28, default=11, suffix="pt", preview=False),
        ],
    ),
    FormatSection(
        "Dropdown",
        [
            FormatField("dropdownIconColor", "Icon Color", "color", default="#252423", preview=False),
            FormatField("dropdownBorderColor", "Border Color", "color", default="#C8C6C4", preview=False),
        ],
    ),
]

# Page & report: filter-pane / filter-card / wallpaper theming. These export to
# the outspacePane / filterCard / outspace cards; there is no live mockup, so
# every field is export-only (preview=False).
_FILTER_PANE_FIELDS = [
    FormatField("filterPaneBackground", "Background", "color", default="#FFFFFF", preview=False),
    FormatField("filterPaneText", "Text Color", "color", default="#252423", preview=False),
    FormatField("filterPaneTransparency", "Transparency", "number", min_val=0, max_val=100, default=0, suffix="%", preview=False),
    FormatField("filterPaneTitleSize", "Title Size", "number", min_val=8, max_val=60, default=12, suffix="pt", preview=False),
    FormatField("filterPaneHeaderSize", "Header Size", "number", min_val=8, max_val=60, default=10, suffix="pt", preview=False),
    FormatField("filterPaneFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    FormatField("filterPaneBorder", "Show Border", "boolean", default=False, preview=False),
    FormatField("filterPaneBorderColor", "Border Color", "color", default="#CCCCCC", preview=False),
    FormatField("filterPaneControlColor", "Apply / Checkbox Color", "color", default="#118DFF", preview=False),
    FormatField("filterPaneInputColor", "Input Box Color", "color", default="#252423", preview=False),
]
_FILTER_CARD_FIELDS = [
    FormatField("filterCardBackground", "Background", "color", default="#FFFFFF", preview=False),
    FormatField("filterCardText", "Text Color", "color", default="#252423", preview=False),
    FormatField("filterCardBorder", "Show Border", "boolean", default=False, preview=False),
    FormatField("filterCardBorderColor", "Border Color", "color", default="#CCCCCC", preview=False),
    FormatField("filterCardTransparency", "Transparency", "number", min_val=0, max_val=100, default=0, suffix="%", preview=False),
    FormatField("filterCardInputColor", "Input Box Color", "color", default="#252423", preview=False),
]
PAGE_SECTIONS = [
    FormatSection("Wallpaper", [
        FormatField("wallpaperColor", "Wallpaper Color", "color", default="#EAEAEA", preview=False),
        FormatField("wallpaperTransparency", "Wallpaper Transparency", "number", min_val=0, max_val=100, default=0, suffix="%", preview=False),
    ]),
    FormatSection("Filter Pane", list(_FILTER_PANE_FIELDS)),
    FormatSection("Filter Cards", list(_FILTER_CARD_FIELDS)),
]
REPORT_SECTIONS = [
    FormatSection("Filter Pane", list(_FILTER_PANE_FIELDS)),
    FormatSection("Filter Cards", list(_FILTER_CARD_FIELDS)),
]

_UNIT_OPTIONS = [("1", "None"), ("1000", "Thousands"), ("1000000", "Millions"),
                 ("1000000000", "Billions")]

# New card visual (cardVisual): callout value, category label, accent bar.
CARD_VISUAL_SECTIONS = [
    FormatSection("Callout Value", [
        FormatField("cvCalloutColor", "Color", "color", default="#252423", preview=False),
        FormatField("cvCalloutSize", "Font Size", "number", min_val=8, max_val=60, default=27, suffix="pt", preview=False),
        FormatField("cvCalloutFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
        FormatField("cvCalloutUnits", "Display Units", "dropdown", options=_UNIT_OPTIONS, preview=False),
        FormatField("cvCalloutPrecision", "Decimal Places", "number", min_val=0, max_val=4, default=0, preview=False),
    ]),
    FormatSection("Category Label", [
        FormatField("cvCatShow", "Show", "boolean", default=True, preview=False),
        FormatField("cvCatColor", "Color", "color", default="#605E5C", preview=False),
        FormatField("cvCatSize", "Font Size", "number", min_val=8, max_val=60, default=10, suffix="pt", preview=False),
        FormatField("cvCatFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
    FormatSection("Accent Bar", [
        FormatField("cvAccentShow", "Show", "boolean", default=False, preview=False),
        FormatField("cvAccentColor", "Color", "color", default="#118DFF", preview=False),
    ]),
]

# New slicer visuals (advanced / list / text): header + items.
NEW_SLICER_SECTIONS = [
    FormatSection("Header", [
        FormatField("nsHeaderShow", "Show", "boolean", default=True, preview=False),
        FormatField("nsHeaderColor", "Font Color", "color", default="#252423", preview=False),
        FormatField("nsHeaderBg", "Background", "color", default="#FFFFFF", preview=False),
        FormatField("nsHeaderSize", "Font Size", "number", min_val=8, max_val=60, default=10, suffix="pt", preview=False),
        FormatField("nsHeaderFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
    FormatSection("Items", [
        FormatField("nsItemsColor", "Font Color", "color", default="#252423", preview=False),
        FormatField("nsItemsBg", "Background", "color", default="#FFFFFF", preview=False),
        FormatField("nsItemsSize", "Font Size", "number", min_val=8, max_val=60, default=11, suffix="pt", preview=False),
        FormatField("nsItemsFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
]

# Navigator visuals (page / bookmark): button fill, text, outline.
NAVIGATOR_SECTIONS = [
    FormatSection("Button Fill", [
        FormatField("navFillColor", "Fill Color", "color", default="#118DFF", preview=False),
    ]),
    FormatSection("Button Text", [
        FormatField("navTextColor", "Font Color", "color", default="#FFFFFF", preview=False),
        FormatField("navTextSize", "Font Size", "number", min_val=8, max_val=60, default=12, suffix="pt", preview=False),
        FormatField("navTextFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
    FormatSection("Button Outline", [
        FormatField("navOutlineColor", "Outline Color", "color", default="#333333", preview=False),
    ]),
]

# Scorecard (Goals): column headers, metric name, current value, target.
SCORECARD_SECTIONS = [
    FormatSection("Column Headers", [
        FormatField("scColHdrColor", "Font Color", "color", default="#252423", preview=False),
        FormatField("scColHdrBg", "Background", "color", default="#FFFFFF", preview=False),
        FormatField("scColHdrSize", "Font Size", "number", min_val=8, max_val=60, default=10, suffix="pt", preview=False),
        FormatField("scColHdrFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
    FormatSection("Metric Name", [
        FormatField("scMetricColor", "Font Color", "color", default="#252423", preview=False),
        FormatField("scMetricSize", "Font Size", "number", min_val=8, max_val=60, default=11, suffix="pt", preview=False),
        FormatField("scMetricFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
    FormatSection("Current Value", [
        FormatField("scCurrentColor", "Font Color", "color", default="#252423", preview=False),
        FormatField("scCurrentSize", "Font Size", "number", min_val=8, max_val=60, default=11, suffix="pt", preview=False),
    ]),
    FormatSection("Target", [
        FormatField("scTargetColor", "Font Color", "color", default="#605E5C", preview=False),
        FormatField("scTargetSize", "Font Size", "number", min_val=8, max_val=60, default=11, suffix="pt", preview=False),
    ]),
]

# Filter visual: header + items.
FILTER_SECTIONS = [
    FormatSection("Header", [
        FormatField("fltHeaderColor", "Font Color", "color", default="#252423", preview=False),
        FormatField("fltHeaderSize", "Font Size", "number", min_val=8, max_val=60, default=10, suffix="pt", preview=False),
        FormatField("fltHeaderFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
    FormatSection("Items", [
        FormatField("fltItemsColor", "Font Color", "color", default="#252423", preview=False),
        FormatField("fltItemsSize", "Font Size", "number", min_val=8, max_val=60, default=10, suffix="pt", preview=False),
        FormatField("fltItemsFont", "Font Family", "dropdown", options=FONT_OPTIONS, default="Segoe UI", preview=False),
    ]),
]

# Group / paginated (RDL) containers only meaningfully theme background + border.
GROUP_SECTIONS = [
    FormatSection("Container", [
        FormatField("grpBgColor", "Background Color", "color", default="#FFFFFF", preview=False),
        FormatField("grpBgTransparency", "Background Transparency", "number", min_val=0, max_val=100, default=0, suffix="%", preview=False),
        FormatField("grpBorderColor", "Border Color", "color", default="#333333", preview=False),
        FormatField("grpBorderRadius", "Rounded Corners", "number", min_val=0, max_val=30, default=0, suffix="px", preview=False),
    ]),
]
RDL_SECTIONS = [
    FormatSection("Report Frame", [
        FormatField("rdlBgColor", "Background Color", "color", default="#FFFFFF", preview=False),
        FormatField("rdlBgTransparency", "Background Transparency", "number", min_val=0, max_val=100, default=0, suffix="%", preview=False),
        FormatField("rdlBorderColor", "Border Color", "color", default="#333333", preview=False),
    ]),
]

# Map visual types to their formatting sections
VISUAL_FORMATTING = {
    # Matrix and Table
    "matrix": MATRIX_TABLE_SECTIONS,
    "table": MATRIX_TABLE_SECTIONS,
    "tableEx": MATRIX_TABLE_SECTIONS,
    "pivotTable": MATRIX_TABLE_SECTIONS,

    # Page & report level (filter pane / cards / wallpaper) -- export-only
    "page": PAGE_SECTIONS,
    "report": REPORT_SECTIONS,

    # Newer / navigation visuals -- export-only
    "cardVisual": CARD_VISUAL_SECTIONS,
    "advancedSlicerVisual": NEW_SLICER_SECTIONS,
    "listSlicer": NEW_SLICER_SECTIONS,
    "textSlicer": NEW_SLICER_SECTIONS,
    "pageNavigator": NAVIGATOR_SECTIONS,
    "bookmarkNavigator": NAVIGATOR_SECTIONS,
    "scorecard": SCORECARD_SECTIONS,
    "filter": FILTER_SECTIONS,
    "group": GROUP_SECTIONS,
    "rdlVisual": RDL_SECTIONS,

    # Charts (cartesian charts carry the small-multiples layout card)
    "barChart": CHART_SECTIONS_SM,
    "clusteredBarChart": CHART_SECTIONS_SM,
    "hundredPercentStackedBarChart": CHART_SECTIONS_SM,
    "columnChart": CHART_SECTIONS_SM,
    "clusteredColumnChart": CHART_SECTIONS_SM,
    "hundredPercentStackedColumnChart": CHART_SECTIONS_SM,
    "lineChart": CHART_SECTIONS_SM,
    "lineClusteredColumnComboChart": CHART_SECTIONS_SM,
    "lineStackedColumnComboChart": CHART_SECTIONS_SM,
    "areaChart": CHART_SECTIONS_SM,
    "stackedAreaChart": CHART_SECTIONS_SM,
    "hundredPercentStackedAreaChart": CHART_SECTIONS_SM,
    "scatterChart": SCATTER_SECTIONS,
    "ribbonChart": CHART_SECTIONS_SM,
    "waterfallChart": WATERFALL_SECTIONS,

    # Charts without cartesian axes -- their own settings sets
    "pieChart": PIE_SECTIONS,
    "donutChart": PIE_SECTIONS,
    "treemap": TREEMAP_SECTIONS,
    "funnel": FUNNEL_SECTIONS,
    "gauge": GAUGE_SECTIONS,

    # Cards and KPIs
    "card": CARD_KPI_SECTIONS,
    "kpi": KPI_SECTIONS,
    "multiRowCard": CARD_KPI_SECTIONS,

    # Slicer
    "slicer": SLICER_SECTIONS,

    # Other visuals (Stage 5)
    "actionButton": ACTION_BUTTON_SECTIONS,
    "basicShape": SHAPE_SECTIONS,
    "decompositionTreeVisual": DECOMP_SECTIONS,
    "map": MAP_SECTIONS,
    "filledMap": FILLED_MAP_SECTIONS,
    "shapeMap": SHAPE_MAP_SECTIONS,
    "image": IMAGE_SECTIONS,
    "textbox": TEXTBOX_SECTIONS,
    "smartNarrative": SMART_NARRATIVE_SECTIONS,
}


def get_formatting_sections(visual_key: str) -> list[FormatSection] | None:
    """Get formatting sections for a visual type, or None if not customizable."""
    return VISUAL_FORMATTING.get(visual_key)


def is_visual_customizable(visual_key: str) -> bool:
    """Check if a visual type has custom formatting options."""
    return visual_key in VISUAL_FORMATTING
