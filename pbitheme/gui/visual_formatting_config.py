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


@dataclass
class FormatSection:
    """A section of formatting options (e.g., "Gridlines", "Row Headers")."""

    name: str
    fields: list[FormatField]


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
        ],
    ),
    FormatSection(
        "Row Headers",
        [
            FormatField("rowHeaderBackgroundColor", "Background Color", "color", default="#F5F5F5"),
            FormatField("rowHeaderTextColor", "Text Color", "color", default="#252423"),
            FormatField("rowHeaderFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("rowHeaderFontBold", "Bold", "boolean", default=False),
        ],
    ),
    FormatSection(
        "Column Headers",
        [
            FormatField("columnHeaderBackgroundColor", "Background Color", "color", default="#F5F5F5"),
            FormatField("columnHeaderTextColor", "Text Color", "color", default="#252423"),
            FormatField("columnHeaderFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("columnHeaderFontBold", "Bold", "boolean", default=False),
            FormatField("columnHeaderAlignment", "Alignment", "dropdown",
                       options=[("Left", "Left"), ("Center", "Center"), ("Right", "Right")]),
        ],
    ),
    FormatSection(
        "Values",
        [
            FormatField("valuesBackgroundColor", "Background Color", "color", default="#FFFFFF"),
            FormatField("valuesTextColor", "Text Color", "color", default="#252423"),
            FormatField("valuesFontSize", "Font Size (pt)", "number", min_val=8, max_val=28, suffix="pt"),
            FormatField("valuesAlignment", "Alignment", "dropdown",
                       options=[("Left", "Left"), ("Center", "Center"), ("Right", "Right")]),
            FormatField("cellPadding", "Cell Padding (px)", "number", min_val=2, max_val=20, suffix="px"),
            FormatField("bandedRows", "Banded Rows", "boolean", default=False),
            FormatField("alternateRowColor", "Alternate Row Color", "color", default="#F5F5F5"),
        ],
    ),
    FormatSection(
        "Totals",
        [
            FormatField("showTotals", "Show Totals", "boolean", default=True),
            FormatField("totalsBackgroundColor", "Background Color", "color", default="#E8E8E8"),
            FormatField("totalsTextColor", "Text Color", "color", default="#000000"),
            FormatField("totalsFontBold", "Bold", "boolean", default=True),
        ],
    ),
    FormatSection(
        "Subtotals",
        [
            FormatField("showSubtotals", "Show Subtotals", "boolean", default=True),
            FormatField("subtotalsBackgroundColor", "Background Color", "color", default="#F0F0F0"),
            FormatField("subtotalsFontBold", "Bold", "boolean", default=True),
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
    "scatterChart": CHART_SECTIONS,
    "ribbonChart": CHART_SECTIONS,
    "waterfallChart": CHART_SECTIONS,

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
}


def get_formatting_sections(visual_key: str) -> list[FormatSection] | None:
    """Get formatting sections for a visual type, or None if not customizable."""
    return VISUAL_FORMATTING.get(visual_key)


def is_visual_customizable(visual_key: str) -> bool:
    """Check if a visual type has custom formatting options."""
    return visual_key in VISUAL_FORMATTING
