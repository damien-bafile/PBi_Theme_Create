"""SVG mockup generators for Power BI visual types.

Renders simplified but realistic Power BI visual mockups using the current theme
*and* the per-visual style overrides, so the live preview reflects every setting.

Each generator takes two override dicts:

* ``formatting`` -- the flat visual-specific formatting map (the ``formatting`` key
  of a visual's ``"*"`` style object, e.g. ``{"xAxisLabelColor": "#333", ...}``).
* ``generic`` -- unpacked generic overrides (background / border / title /
  data-labels / legend); only the sections the user enabled are present.

Use :func:`render_visual_preview` to render the right mockup for a visual key from
a stored ``"*"`` style object -- both the editor dialog and the main-window preview
panel go through it, so what you see always matches what will be saved.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape

from ..model import (
    PowerBITheme,
    unpack_background_object,
    unpack_border_object,
    unpack_title_object,
    unpack_data_labels_object,
    unpack_legend_object,
)


# --------------------------------------------------------------------------- #
# Small typed accessors (kept tiny so the generators read cleanly)
# --------------------------------------------------------------------------- #
def _col(fmt: Dict[str, Any], key: str, default: str) -> str:
    val = fmt.get(key, default) if fmt else default
    return val if isinstance(val, str) and val else default


def _num(fmt: Dict[str, Any], key: str, default: float) -> float:
    val = fmt.get(key, default) if fmt else default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _flag(fmt: Dict[str, Any], key: str, default: bool) -> bool:
    val = fmt.get(key, default) if fmt else default
    return bool(val)


def _txt(fmt: Dict[str, Any], key: str, default: str) -> str:
    val = fmt.get(key, default) if fmt else default
    return str(val) if val else default


def _esc(text: Any) -> str:
    return escape(str(text))


# --------------------------------------------------------------------------- #
# Generic-override extraction (shared by dialog + main window)
# --------------------------------------------------------------------------- #
def extract_generic(style_obj: Dict[str, Any] | None) -> Dict[str, Any]:
    """Turn a stored ``"*"`` style object into a flat generic-overrides dict.

    Only sections whose ``show`` flag is set are returned, so a caller can treat
    a missing key as "not overridden".
    """
    generic: Dict[str, Any] = {}
    if not style_obj:
        return generic

    # A section counts as overridden only when its key is actually present *and*
    # its show flag is set -- an absent key means "no override" (unpack_* would
    # otherwise report show=True by default for background/title/legend).
    if "background" in style_obj:
        bg_show, bg_color, bg_trans = unpack_background_object(style_obj)
        if bg_show:
            generic["background"] = {"color": bg_color, "transparency": bg_trans}

    if "border" in style_obj:
        border_show, border_color = unpack_border_object(style_obj)
        if border_show:
            generic["border"] = {"color": border_color}

    if "title" in style_obj:
        title_show, title_font, title_size, title_color = unpack_title_object(style_obj)
        if title_show:
            generic["title"] = {"font": title_font, "size": title_size, "color": title_color}

    if "labels" in style_obj:
        labels_show, labels_color, labels_size = unpack_data_labels_object(style_obj)
        if labels_show:
            generic["labels"] = {"color": labels_color, "size": labels_size}

    if "legend" in style_obj:
        legend_show, legend_pos, legend_color = unpack_legend_object(style_obj)
        if legend_show:
            generic["legend"] = {"position": legend_pos, "color": legend_color}

    return generic


def _frame(width: int, height: int, generic: Dict[str, Any], theme_bg: str) -> List[str]:
    """Background rect (+ optional generic background/border) for any mockup."""
    parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    gbg = (generic or {}).get("background")
    if gbg:
        opacity = max(0.0, min(1.0, gbg.get("transparency", 100) / 100.0))
        parts.append(f'<rect width="{width}" height="{height}" fill="{gbg["color"]}" opacity="{opacity:.2f}"/>')
    else:
        parts.append(f'<rect width="{width}" height="{height}" fill="{theme_bg}"/>')
    gborder = (generic or {}).get("border")
    if gborder:
        parts.append(
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
            f'fill="none" stroke="{gborder["color"]}" stroke-width="2"/>'
        )
    return parts


def _title(width: int, default_text: str, default_color: str,
           generic: Dict[str, Any]) -> Tuple[str, int]:
    """Return (title <text> svg, y-offset consumed) honoring a generic title override."""
    gtitle = (generic or {}).get("title")
    color = gtitle["color"] if gtitle else default_color
    size = int(gtitle["size"]) if gtitle else 13
    y = size + 4
    svg = (
        f'<text x="{width // 2}" y="{y}" font-size="{size}" fill="{color}" '
        f'text-anchor="middle" font-weight="bold">{_esc(default_text)}</text>'
    )
    return svg, y + 4


def _legend(x: int, y: int, colors: List[str], formatting: Dict[str, Any],
            generic: Dict[str, Any], horizontal: bool) -> List[str]:
    """Render a small 3-series legend at (x, y)."""
    gleg = (generic or {}).get("legend")
    color = gleg["color"] if gleg else _col(formatting, "legendTextColor", "#252423")
    size = int(_num(formatting, "legendFontSize", 10))
    names = ["Series A", "Series B", "Series C"]
    parts: List[str] = []
    cx, cy = x, y
    for i, name in enumerate(names[: len(colors)]):
        parts.append(f'<rect x="{cx}" y="{cy - size + 2}" width="{size}" height="{size}" fill="{colors[i]}"/>')
        parts.append(
            f'<text x="{cx + size + 3}" y="{cy}" font-size="{size}" fill="{color}">{name}</text>'
        )
        if horizontal:
            cx += size + 12 + len(name) * size * 0.55
        else:
            cy += size + 6
    return parts


def _legend_position(formatting: Dict[str, Any], generic: Dict[str, Any]) -> str:
    gleg = (generic or {}).get("legend")
    if gleg:
        return gleg.get("position", "Top")
    return _txt(formatting, "legendPosition", "Top")


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def _chart_base(
    theme: PowerBITheme,
    formatting: Dict[str, Any],
    generic: Dict[str, Any],
    width: int,
    height: int,
    title_text: str,
) -> Tuple[List[str], int, int, int, int]:
    """Shared chart chrome: frame, title, legend, axes, gridlines, axis titles/labels.

    Returns (svg_parts, plot_left, plot_top, plot_right, plot_bottom).
    """
    formatting = formatting or {}
    generic = generic or {}
    fg = theme.foreground
    colors = (theme.data_colors[:3] or [theme.table_accent]) if theme.data_colors else [theme.table_accent]
    while len(colors) < 3:
        colors.append(colors[0])

    parts = _frame(width, height, generic, theme.background)
    title_svg, top_used = _title(width, title_text, fg, generic)

    legend_pos = _legend_position(formatting, generic)

    # Plot margins -- widen where a legend / axis title needs room.
    left = 44                      # y-axis labels + title
    right = 12
    top = top_used + 6
    bottom = 40                    # x-axis labels + title
    if legend_pos == "Top":
        top += 16
    elif legend_pos == "Bottom":
        bottom += 16
    elif legend_pos == "Left":
        left += 60
    elif legend_pos == "Right":
        right += 60

    plot_l, plot_t = left, top
    plot_r, plot_b = width - right, height - bottom

    # ---- Gridlines (horizontal) ---- #
    g_style = _txt(formatting, "gridlineStyle", "None")
    if g_style != "None":
        g_color = _col(formatting, "gridlineColor", "#CCCCCC")
        g_th = _num(formatting, "gridlineThickness", 1)
        dash = ' stroke-dasharray="4,3"' if g_style == "Dashed" else ""
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            gy = plot_b - frac * (plot_b - plot_t)
            parts.append(
                f'<line x1="{plot_l}" y1="{gy:.1f}" x2="{plot_r}" y2="{gy:.1f}" '
                f'stroke="{g_color}" stroke-width="{g_th}"{dash}/>'
            )

    # ---- Axes ---- #
    parts.append(f'<line x1="{plot_l}" y1="{plot_b}" x2="{plot_r}" y2="{plot_b}" stroke="{fg}" stroke-width="1"/>')
    parts.append(f'<line x1="{plot_l}" y1="{plot_t}" x2="{plot_l}" y2="{plot_b}" stroke="{fg}" stroke-width="1"/>')

    # ---- Y-axis labels + title ---- #
    y_lab_color = _col(formatting, "yAxisLabelColor", fg)
    y_lab_size = int(_num(formatting, "yAxisLabelFontSize", 8))
    for frac, val in ((0.0, "0"), (0.5, "50"), (1.0, "100")):
        gy = plot_b - frac * (plot_b - plot_t)
        parts.append(
            f'<text x="{plot_l - 4}" y="{gy + y_lab_size / 3:.1f}" font-size="{y_lab_size}" '
            f'fill="{y_lab_color}" text-anchor="end">{val}</text>'
        )
    y_title_color = _col(formatting, "yAxisTitleColor", fg)
    y_title_size = int(_num(formatting, "yAxisTitleFontSize", 8))
    ty = (plot_t + plot_b) / 2
    parts.append(
        f'<text x="10" y="{ty:.1f}" font-size="{y_title_size}" fill="{y_title_color}" '
        f'text-anchor="middle" transform="rotate(-90 10 {ty:.1f})">Value</text>'
    )

    # ---- X-axis labels + title ---- #
    x_lab_color = _col(formatting, "xAxisLabelColor", fg)
    x_lab_size = int(_num(formatting, "xAxisLabelFontSize", 8))
    cats = ["Q1", "Q2", "Q3", "Q4"]
    span = (plot_r - plot_l) / len(cats)
    for i, cat in enumerate(cats):
        cx = plot_l + span * (i + 0.5)
        parts.append(
            f'<text x="{cx:.1f}" y="{plot_b + x_lab_size + 4}" font-size="{x_lab_size}" '
            f'fill="{x_lab_color}" text-anchor="middle">{cat}</text>'
        )
    x_title_color = _col(formatting, "xAxisTitleColor", fg)
    x_title_size = int(_num(formatting, "xAxisTitleFontSize", 8))
    parts.append(
        f'<text x="{(plot_l + plot_r) / 2:.1f}" y="{height - 4}" font-size="{x_title_size}" '
        f'fill="{x_title_color}" text-anchor="middle">Category</text>'
    )

    # ---- Legend ---- #
    if legend_pos == "Top":
        parts += _legend(plot_l, top_used + 12, colors, formatting, generic, horizontal=True)
    elif legend_pos == "Bottom":
        parts += _legend(plot_l, height - 22, colors, formatting, generic, horizontal=True)
    elif legend_pos == "Left":
        parts += _legend(6, plot_t + 10, colors, formatting, generic, horizontal=False)
    elif legend_pos == "Right":
        parts += _legend(plot_r + 8, plot_t + 10, colors, formatting, generic, horizontal=False)

    parts.append(title_svg)
    return parts, plot_l, plot_t, plot_r, plot_b


def generate_bar_chart_svg(
    theme: PowerBITheme,
    formatting: Dict[str, Any] | None = None,
    generic: Dict[str, Any] | None = None,
    width: int = 300,
    height: int = 200,
) -> str:
    """Bar chart honoring axes, gridlines, data labels, legend, title & background."""
    formatting = formatting or {}
    generic = generic or {}
    colors = (theme.data_colors[:3] or [theme.table_accent]) if theme.data_colors else [theme.table_accent]
    while len(colors) < 3:
        colors.append(colors[0])

    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Bar Chart")

    groups = [[70, 55, 40], [85, 65, 50], [65, 75, 60], [90, 80, 70]]
    span = (pr - pl) / len(groups)
    bar_w = span / 4.2
    scale = (pb - pt) / 100.0

    show_labels = bool(generic.get("labels")) or bool(formatting.get("dataLabelColor"))
    dl_color = generic["labels"]["color"] if generic.get("labels") else _col(formatting, "dataLabelColor", "#252423")
    dl_size = int(generic["labels"]["size"]) if generic.get("labels") else int(_num(formatting, "dataLabelFontSize", 8))
    dl_bg = _flag(formatting, "dataLabelBackground", False)

    for gi, vals in enumerate(groups):
        base_x = pl + span * gi + span * 0.12
        for si, val in enumerate(vals):
            x = base_x + si * bar_w
            h = val * scale
            y = pb - h
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                f'fill="{colors[si]}" opacity="0.9"/>'
            )
        if show_labels:
            top_val = vals[0]
            lx = base_x + bar_w / 2
            ly = pb - top_val * scale - 3
            if dl_bg:
                parts.append(
                    f'<rect x="{lx - 9:.1f}" y="{ly - dl_size:.1f}" width="18" height="{dl_size + 3}" '
                    f'fill="#FFFFFF" opacity="0.7"/>'
                )
            parts.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="{dl_size}" fill="{dl_color}" '
                f'text-anchor="middle">{top_val}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def generate_line_chart_svg(
    theme: PowerBITheme,
    formatting: Dict[str, Any] | None = None,
    generic: Dict[str, Any] | None = None,
    width: int = 300,
    height: int = 200,
) -> str:
    """Line chart honoring the same chart chrome as the bar chart."""
    formatting = formatting or {}
    generic = generic or {}
    colors = (theme.data_colors[:3] or [theme.table_accent]) if theme.data_colors else [theme.table_accent]
    while len(colors) < 3:
        colors.append(colors[0])

    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Line Chart")

    series = [
        [40, 55, 50, 70, 65, 80],
        [30, 40, 45, 55, 60, 68],
        [20, 28, 35, 42, 48, 58],
    ]
    scale = (pb - pt) / 100.0
    n = len(series[0])
    step = (pr - pl) / (n - 1)

    show_labels = bool(generic.get("labels")) or bool(formatting.get("dataLabelColor"))
    dl_color = generic["labels"]["color"] if generic.get("labels") else _col(formatting, "dataLabelColor", "#252423")
    dl_size = int(generic["labels"]["size"]) if generic.get("labels") else int(_num(formatting, "dataLabelFontSize", 8))
    dl_bg = _flag(formatting, "dataLabelBackground", False)

    for si, line in enumerate(series):
        pts = []
        for i, val in enumerate(line):
            x = pl + i * step
            y = pb - val * scale
            pts.append(f"{x:.1f},{y:.1f}")
        parts.append(
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{colors[si]}" '
            f'stroke-width="2" opacity="0.9"/>'
        )
        if show_labels and si == 0:
            for i, val in enumerate(line):
                x = pl + i * step
                y = pb - val * scale - 3
                if dl_bg:
                    parts.append(
                        f'<rect x="{x - 9:.1f}" y="{y - dl_size:.1f}" width="18" height="{dl_size + 3}" '
                        f'fill="#FFFFFF" opacity="0.7"/>'
                    )
                parts.append(
                    f'<text x="{x:.1f}" y="{y:.1f}" font-size="{dl_size}" fill="{dl_color}" '
                    f'text-anchor="middle">{val}</text>'
                )

    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Table / Matrix
# --------------------------------------------------------------------------- #
def generate_table_svg(
    theme: PowerBITheme,
    formatting: Dict[str, Any] | None = None,
    generic: Dict[str, Any] | None = None,
    width: int = 300,
    height: int = 200,
) -> str:
    """Table/matrix honoring every gridline, header, values, totals & subtotals field."""
    formatting = formatting or {}
    generic = generic or {}
    fg = theme.foreground
    accent = theme.table_accent

    # --- Field values --- #
    grid_style = _txt(formatting, "gridlineStyle", "Solid")
    grid_color = _col(formatting, "gridlineColor", fg)
    grid_th = _num(formatting, "gridlineThickness", 1)
    row_spacing = _num(formatting, "rowSpacing", 0)

    rh_bg = _col(formatting, "rowHeaderBackgroundColor", "#F5F5F5")
    rh_fg = _col(formatting, "rowHeaderTextColor", fg)
    rh_size = int(_num(formatting, "rowHeaderFontSize", 11))
    rh_bold = _flag(formatting, "rowHeaderFontBold", False)

    ch_bg = _col(formatting, "columnHeaderBackgroundColor", accent)
    ch_fg = _col(formatting, "columnHeaderTextColor", fg)
    ch_size = int(_num(formatting, "columnHeaderFontSize", 12))
    ch_bold = _flag(formatting, "columnHeaderFontBold", True)
    ch_align = _txt(formatting, "columnHeaderAlignment", "Left")

    v_bg = _col(formatting, "valuesBackgroundColor", theme.background)
    v_fg = _col(formatting, "valuesTextColor", fg)
    v_size = int(_num(formatting, "valuesFontSize", 11))
    v_align = _txt(formatting, "valuesAlignment", "Left")
    padding = _num(formatting, "cellPadding", 6)

    show_totals = _flag(formatting, "showTotals", True)
    tot_bg = _col(formatting, "totalsBackgroundColor", "#E8E8E8")
    tot_fg = _col(formatting, "totalsTextColor", "#000000")
    tot_bold = _flag(formatting, "totalsFontBold", True)

    show_sub = _flag(formatting, "showSubtotals", True)
    sub_bg = _col(formatting, "subtotalsBackgroundColor", "#F0F0F0")
    sub_bold = _flag(formatting, "subtotalsFontBold", True)

    def anchor(a: str) -> Tuple[str, float]:
        return {"Left": ("start", 0.08), "Center": ("middle", 0.5), "Right": ("end", 0.92)}.get(
            a, ("start", 0.08)
        )

    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Table", fg, generic)

    cols = ["Region", "Sales", "Status"]
    body = [
        ("North", "125.5", "Good"),
        ("South", "98.3", "Neutral"),
    ]
    sub_row = ("Subtotal", "223.8", "")
    data2 = [
        ("East", "156.7", "Good"),
        ("West", "72.1", "Bad"),
    ]
    tot_row = ("Total", "452.6", "")

    col_w = width / len(cols)
    row_h = max(16, v_size + padding * 2 + row_spacing)
    header_h = max(18, ch_size + padding * 2)
    y = top

    def draw_row(vals, bg, text_color, size, bold, align, is_header=False):
        nonlocal y
        h = header_h if is_header else row_h
        parts.append(f'<rect x="0" y="{y:.1f}" width="{width}" height="{h:.1f}" fill="{bg}" opacity="0.55"/>')
        weight = "bold" if bold else "normal"
        for ci, cell in enumerate(vals):
            if cell == "":
                continue
            # First column follows row-header styling for body rows.
            if ci == 0 and not is_header:
                anc, fx = anchor("Left")
                tx = col_w * ci + col_w * fx
                parts.append(
                    f'<text x="{tx:.1f}" y="{y + h * 0.66:.1f}" font-size="{rh_size}" '
                    f'fill="{rh_fg}" font-weight="{"bold" if rh_bold else "normal"}" '
                    f'text-anchor="{anc}">{_esc(cell)}</text>'
                )
                continue
            anc, fx = anchor(align)
            tx = col_w * ci + col_w * fx
            parts.append(
                f'<text x="{tx:.1f}" y="{y + h * 0.66:.1f}" font-size="{size}" fill="{text_color}" '
                f'font-weight="{weight}" text-anchor="{anc}">{_esc(cell)}</text>'
            )
        # gridline under the row
        if grid_style != "None":
            dash = ' stroke-dasharray="3,3"' if grid_style == "Dashed" else ""
            parts.append(
                f'<line x1="0" y1="{y + h:.1f}" x2="{width}" y2="{y + h:.1f}" '
                f'stroke="{grid_color}" stroke-width="{grid_th}"{dash}/>'
            )
        y += h

    # Header row (row-header bg tints the first cell area).
    parts.append(f'<rect x="0" y="{y:.1f}" width="{col_w:.1f}" height="{header_h:.1f}" fill="{rh_bg}" opacity="0.7"/>')
    draw_row(cols, ch_bg, ch_fg, ch_size, ch_bold, ch_align, is_header=True)

    for row in body:
        draw_row(row, v_bg, v_fg, v_size, False, v_align)
    if show_sub:
        draw_row(sub_row, sub_bg, v_fg, v_size, sub_bold, v_align)
    for row in data2:
        draw_row(row, v_bg, v_fg, v_size, False, v_align)
    if show_totals:
        draw_row(tot_row, tot_bg, tot_fg, v_size, tot_bold, v_align)

    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Card / KPI
# --------------------------------------------------------------------------- #
def generate_card_kpi_svg(
    theme: PowerBITheme,
    formatting: Dict[str, Any] | None = None,
    generic: Dict[str, Any] | None = None,
    width: int = 300,
    height: int = 200,
) -> str:
    """Card/KPI honoring value, label and background formatting."""
    formatting = formatting or {}
    generic = generic or {}
    fg = theme.foreground

    value_color = _col(formatting, "valueColor", theme.good)
    value_size = int(_num(formatting, "valueFontSize", 36))
    value_bold = _flag(formatting, "valueFontBold", True)
    label_color = _col(formatting, "labelColor", fg)
    label_size = int(_num(formatting, "labelFontSize", 13))
    card_bg = _col(formatting, "backgroundColor", "#FFFFFF")
    show_border = _flag(formatting, "backgroundBorder", False)

    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Card / KPI", fg, generic)

    pad = 18
    card_top = top + 4
    card_h = height - card_top - 14
    stroke = f' stroke="{fg}" stroke-width="1"' if show_border else ""
    parts.append(
        f'<rect x="{pad}" y="{card_top}" width="{width - pad * 2}" height="{card_h}" '
        f'rx="4" fill="{card_bg}"{stroke}/>'
    )

    cx = width // 2
    vy = card_top + card_h * 0.45
    weight = "bold" if value_bold else "normal"
    parts.append(
        f'<text x="{cx}" y="{vy:.0f}" font-size="{value_size}" fill="{value_color}" '
        f'text-anchor="middle" font-weight="{weight}">$1.2M</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{vy + value_size * 0.75:.0f}" font-size="{label_size}" '
        f'fill="{label_color}" text-anchor="middle">Revenue (YTD)</text>'
    )

    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
_TABLE_KEYS = {"matrix", "table", "tableEx", "pivotTable"}
_CARD_KEYS = {"card", "kpi", "multiRowCard"}
_LINE_KEYS = {"lineChart", "lineClusteredColumnComboChart", "lineStackedColumnComboChart", "areaChart"}


def render_visual_preview(
    theme: PowerBITheme,
    visual_key: str,
    style_obj: Dict[str, Any] | None = None,
    width: int = 250,
    height: int = 200,
) -> str:
    """Render the appropriate mockup for *visual_key* from a stored ``"*"`` style object."""
    style_obj = style_obj or {}
    formatting = style_obj.get("formatting", {}) if isinstance(style_obj, dict) else {}
    generic = extract_generic(style_obj)

    if visual_key in _TABLE_KEYS:
        return generate_table_svg(theme, formatting, generic, width, height)
    if visual_key in _CARD_KEYS:
        return generate_card_kpi_svg(theme, formatting, generic, width, height)
    if visual_key in _LINE_KEYS:
        return generate_line_chart_svg(theme, formatting, generic, width, height)
    return generate_bar_chart_svg(theme, formatting, generic, width, height)


def generate_all_mockups(
    theme: PowerBITheme,
    visual_styles: Dict[str, Any] | None = None,
    size: int = 300,
) -> dict[str, str]:
    """Generate the four main-window mockups, each honoring its visual's stored styles."""
    visual_styles = visual_styles or {}
    w, h = size, int(size * 0.7)

    def style_for(*keys: str) -> Dict[str, Any]:
        for k in keys:
            entry = visual_styles.get(k)
            if entry:
                return entry.get("*", entry)
        return {}

    return {
        "bar_chart": render_visual_preview(theme, "barChart", style_for("barChart", "columnChart", "clusteredBarChart"), w, h),
        "table": render_visual_preview(theme, "table", style_for("table", "matrix", "tableEx", "pivotTable"), w, h),
        "line_chart": render_visual_preview(theme, "lineChart", style_for("lineChart", "areaChart"), w, h),
        "card_kpi": render_visual_preview(theme, "card", style_for("card", "kpi", "multiRowCard"), w, h),
    }
