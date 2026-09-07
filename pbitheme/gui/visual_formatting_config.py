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
]

# Chart formatting sections
CHART_SECTIONS = [
    FormatSection(
        "X-Axis",
        [
            FormatField("xAxisTitleText", "Title Text", "text", default=""),
            FormatField("xAxisLabelColor", "Label Color", "color", default="#252423"),
            FormatField("xAxisLabelFontSize", "Font Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
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
]

# Scatter = chart sections plus marker / bubble options.
SCATTER_SECTIONS = CHART_SECTIONS + [
    FormatSection(
        "Markers",
        [
            FormatField("bubbleSize", "Bubble Size", "number", min_val=0, max_val=100, default=20),
            FormatField("markerBorderColor", "Border Color", "color", default="#FFFFFF"),
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
        ],
    ),
    FormatSection(
        "Data Labels",
        [
            FormatField("showDataLabels", "Show Labels", "boolean", default=True),
            FormatField("dataLabelColor", "Color", "color", default="#FFFFFF"),
            FormatField("dataLabelFontSize", "Font Size (pt)", "number", min_val=6, max_val=16, suffix="pt"),
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
        ],
    ),
    FormatSection(
        "Data Labels",
        [
            FormatField("showDataLabels", "Show Labels", "boolean", default=True),
            FormatField("dataLabelColor", "Color", "color", default="#FFFFFF"),
            FormatField("dataLabelFontSize", "Font Size (pt)", "number", min_val=6, max_val=16, suffix="pt"),
        ],
    ),
]

# Funnel -- decreasing stages; bar colour + data labels.
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

# Map visual types to their formatting sections
VISUAL_FORMATTING = {
    # Matrix and Table
    "matrix": MATRIX_TABLE_SECTIONS,
    "table": MATRIX_TABLE_SECTIONS,
    "tableEx": MATRIX_TABLE_SECTIONS,
    "pivotTable": MATRIX_TABLE_SECTIONS,

    # Charts
    "barChart": CHART_SECTIONS,
    "clusteredBarChart": CHART_SECTIONS,
    "hundredPercentStackedBarChart": CHART_SECTIONS,
    "columnChart": CHART_SECTIONS,
    "clusteredColumnChart": CHART_SECTIONS,
    "hundredPercentStackedColumnChart": CHART_SECTIONS,
    "lineChart": CHART_SECTIONS,
    "lineClusteredColumnComboChart": CHART_SECTIONS,
    "lineStackedColumnComboChart": CHART_SECTIONS,
    "areaChart": CHART_SECTIONS,
    "scatterChart": SCATTER_SECTIONS,
    "ribbonChart": CHART_SECTIONS,
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
