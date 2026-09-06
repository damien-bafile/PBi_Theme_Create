"""SVG mockup generators for Power BI visual types.

Renders simplified but realistic Power BI visual mockups using the current theme.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..model import PowerBITheme


def generate_bar_chart_svg(theme: PowerBITheme, width: int = 300, height: int = 200) -> str:
    """Generate SVG for a bar chart showing data colors."""
    bg = theme.background
    fg = theme.foreground
    accent = theme.table_accent
    colors = theme.data_colors[:3] if theme.data_colors else [accent]

    # Ensure we have colors
    if not colors:
        colors = ["#118DFF"]

    # Normalize to 3 colors for consistent rendering
    while len(colors) < 3:
        colors.append(colors[0])
    colors = colors[:3]

    bars = [
        {"label": "Q1", "values": [70, 55, 40]},
        {"label": "Q2", "values": [85, 65, 50]},
        {"label": "Q3", "values": [65, 75, 60]},
        {"label": "Q4", "values": [90, 80, 70]},
    ]

    # Calculate bar positions
    bar_width = (width - 40) / (len(bars) * 3 + 10)
    max_val = 100
    scale = (height - 60) / max_val

    svg_parts = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
    ]

    # Draw bars
    x_offset = 20
    for bar_idx, bar in enumerate(bars):
        for series_idx, val in enumerate(bar["values"]):
            x = x_offset + bar_idx * (bar_width * 3 + 10) + series_idx * bar_width
            bar_height = val * scale
            y = height - 40 - bar_height
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" '
                f'fill="{colors[series_idx]}" opacity="0.8"/>'
            )

    # Draw axes and labels
    svg_parts.append(f'<line x1="20" y1="{height - 40}" x2="{width - 20}" y2="{height - 40}" stroke="{fg}" stroke-width="1"/>')
    svg_parts.append(f'<line x1="20" y1="20" x2="20" y2="{height - 40}" stroke="{fg}" stroke-width="1"/>')

    # Add title
    title_font = next((tc for name, tc in theme.text_classes.items() if name == "title"), None)
    title_size = title_font.font_size if title_font else 14
    svg_parts.append(
        f'<text x="{width // 2}" y="20" font-size="{title_size}" fill="{fg}" '
        f'text-anchor="middle" font-weight="bold">Bar Chart</text>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_table_svg(
    theme: PowerBITheme,
    visual_styles: Dict[str, Any] | None = None,
    width: int = 300,
    height: int = 200
) -> str:
    """Generate SVG for a table showing structural colors and text."""
    visual_styles = visual_styles or {}

    # Extract formatting from visual_styles (from "*" key)
    formatting = visual_styles.get("*", {}).get("formatting", {})

    bg = theme.background
    fg = theme.foreground
    accent = theme.table_accent

    # Use custom colors from formatting if available
    col_header_bg = formatting.get("columnHeaderBackgroundColor", accent)
    col_header_fg = formatting.get("columnHeaderTextColor", fg)
    col_header_size = formatting.get("columnHeaderFontSize", 12)
    col_header_bold = formatting.get("columnHeaderFontBold", True)

    values_bg = formatting.get("valuesBackgroundColor", bg)
    values_fg = formatting.get("valuesTextColor", fg)
    values_size = formatting.get("valuesFontSize", 11)

    gridline_color = formatting.get("gridlineColor", fg)
    gridline_style = formatting.get("gridlineStyle", "Solid")

    col_width = width // 3
    row_height = 30

    svg_parts = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
    ]

    # Header with custom background color
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{row_height}" fill="{col_header_bg}" opacity="0.3"/>'
    )

    headers = ["Name", "Value", "Status"]
    weight = "bold" if col_header_bold else "normal"
    for i, header in enumerate(headers):
        svg_parts.append(
            f'<text x="{col_width * i + 10}" y="22" font-size="{col_header_size}" fill="{col_header_fg}" '
            f'font-weight="{weight}">{header}</text>'
        )

    # Data rows
    rows = [
        ["Item 1", "125.5", "Good"],
        ["Item 2", "98.3", "Neutral"],
        ["Item 3", "156.7", "Good"],
        ["Item 4", "72.1", "Bad"],
    ]

    for row_idx, row in enumerate(rows):
        y = row_height * (row_idx + 1)
        # Alternating row background
        if row_idx % 2 == 0:
            svg_parts.append(f'<rect x="0" y="{y}" width="{width}" height="{row_height}" fill="{values_bg}" opacity="0.5"/>')

        for col_idx, cell in enumerate(row):
            svg_parts.append(
                f'<text x="{col_width * col_idx + 10}" y="{y + 22}" font-size="{values_size}" fill="{values_fg}">{cell}</text>'
            )

        # Row border (gridline)
        stroke_dasharray = "3,3" if gridline_style == "Dashed" else "none"
        dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray != "none" else ""
        svg_parts.append(f'<line x1="0" y1="{y + row_height}" x2="{width}" y2="{y + row_height}" stroke="{gridline_color}" stroke-width="1"{dash_attr}/>')

    # Title
    svg_parts.append(
        f'<text x="{width // 2}" y="{height - 10}" font-size="11" fill="{fg}" '
        f'text-anchor="middle">Table</text>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_line_chart_svg(theme: PowerBITheme, width: int = 300, height: int = 200) -> str:
    """Generate SVG for a line chart showing data colors."""
    bg = theme.background
    fg = theme.foreground
    colors = theme.data_colors[:2] if theme.data_colors else ["#118DFF", "#E66C37"]

    # Ensure we have 2 colors
    if not colors or len(colors) < 2:
        colors = ["#118DFF", "#E66C37"]

    # 12 months of data
    months = list(range(1, 13))
    line1 = [40, 45, 50, 55, 60, 65, 70, 75, 80, 75, 70, 65]
    line2 = [30, 35, 40, 45, 50, 55, 60, 65, 70, 65, 60, 55]

    # Chart area
    chart_left = 30
    chart_top = 20
    chart_width = width - 50
    chart_height = height - 60

    # Scale
    max_val = 100
    x_scale = chart_width / (len(months) - 1) if len(months) > 1 else 1
    y_scale = chart_height / max_val

    svg_parts = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
    ]

    # Draw grid lines (faint)
    for i in range(0, 101, 20):
        y = chart_top + chart_height - (i * y_scale)
        svg_parts.append(
            f'<line x1="{chart_left}" y1="{y}" x2="{chart_left + chart_width}" y2="{y}" '
            f'stroke="{fg}" stroke-width="0.5" opacity="0.2"/>'
        )

    # Draw lines
    for line_data, color in [(line1, colors[0]), (line2, colors[1])]:
        points = []
        for idx, val in enumerate(line_data):
            x = chart_left + (idx * x_scale)
            y = chart_top + chart_height - (val * y_scale)
            points.append(f"{x},{y}")

        svg_parts.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
            f'stroke-width="2" opacity="0.8"/>'
        )

    # Axes
    svg_parts.append(
        f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" '
        f'y2="{chart_top + chart_height}" stroke="{fg}" stroke-width="1"/>'
    )
    svg_parts.append(f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="{fg}" stroke-width="1"/>')

    # Title
    svg_parts.append(
        f'<text x="{width // 2}" y="15" font-size="12" fill="{fg}" '
        f'text-anchor="middle" font-weight="bold">Line Chart</text>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_card_kpi_svg(theme: PowerBITheme, width: int = 300, height: int = 200) -> str:
    """Generate SVG for a card/KPI showing typography and backgrounds."""
    bg = theme.background
    fg = theme.foreground
    good = theme.good

    card_bg = bg if theme.background != "#FFFFFF" else "#F5F5F5"

    svg_parts = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
    ]

    # Card background
    card_padding = 20
    card_height = height - 40
    svg_parts.append(
        f'<rect x="{card_padding}" y="20" width="{width - card_padding * 2}" height="{card_height}" '
        f'fill="{card_bg}" stroke="{fg}" stroke-width="1" opacity="0.8"/>'
    )

    # KPI value
    svg_parts.append(
        f'<text x="{width // 2}" y="80" font-size="36" fill="{good}" '
        f'text-anchor="middle" font-weight="bold">$1.2M</text>'
    )

    # KPI label
    svg_parts.append(
        f'<text x="{width // 2}" y="120" font-size="13" fill="{fg}" '
        f'text-anchor="middle">Revenue (YTD)</text>'
    )

    # Trend indicator
    svg_parts.append(
        f'<text x="{width // 2}" y="160" font-size="12" fill="{good}" '
        f'text-anchor="middle">↑ +12.5%</text>'
    )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def generate_all_mockups(
    theme: PowerBITheme,
    visual_styles: Dict[str, Any] | None = None,
    size: int = 300
) -> dict[str, str]:
    """Generate all 4 mockup SVGs for the current theme and visual styles."""
    visual_styles = visual_styles or {}
    return {
        "bar_chart": generate_bar_chart_svg(theme, width=size, height=int(size * 0.7)),
        "table": generate_table_svg(theme, visual_styles.get("table", {}), width=size, height=int(size * 0.7)),
        "line_chart": generate_line_chart_svg(theme, width=size, height=int(size * 0.7)),
        "card_kpi": generate_card_kpi_svg(theme, width=size, height=int(size * 0.7)),
    }
