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
            FormatField("xAxisLabelColor", "Label Color", "color", default="#252423"),
            FormatField("xAxisLabelFontSize", "Font Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
            FormatField("xAxisTitleColor", "Title Color", "color", default="#252423"),
            FormatField("xAxisTitleFontSize", "Title Size (pt)", "number", min_val=8, max_val=20, suffix="pt"),
        ],
    ),
    FormatSection(
        "Y-Axis",
        [
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
        ],
    ),
    FormatSection(
        "Legend",
        [
            FormatField("legendPosition", "Position", "dropdown",
                       options=[("Top", "Top"), ("Bottom", "Bottom"), ("Left", "Left"), ("Right", "Right")]),
            FormatField("legendTextColor", "Text Color", "color", default="#252423"),
            FormatField("legendFontSize", "Font Size (pt)", "number", min_val=8, max_val=16, suffix="pt"),
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
    "pieChart": CHART_SECTIONS,
    "donutChart": CHART_SECTIONS,
    "ribbonChart": CHART_SECTIONS,
    "treemap": CHART_SECTIONS,
    "waterfallChart": CHART_SECTIONS,
    "funnel": CHART_SECTIONS,
    "gauge": CHART_SECTIONS,

    # Cards and KPIs
    "card": CARD_KPI_SECTIONS,
    "kpi": CARD_KPI_SECTIONS,
    "multiRowCard": CARD_KPI_SECTIONS,
}


def get_formatting_sections(visual_key: str) -> list[FormatSection] | None:
    """Get formatting sections for a visual type, or None if not customizable."""
    return VISUAL_FORMATTING.get(visual_key)


def is_visual_customizable(visual_key: str) -> bool:
    """Check if a visual type has custom formatting options."""
    return visual_key in VISUAL_FORMATTING
