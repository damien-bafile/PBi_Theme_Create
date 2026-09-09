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

import math
import random
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape

from ..model import (
    PowerBITheme,
    unpack_background_object,
    unpack_border_object,
    unpack_drop_shadow_object,
    unpack_visual_header_object,
    unpack_subtitle_object,
    unpack_padding_object,
    unpack_divider_object,
    unpack_title_object,
    unpack_data_labels_object,
    unpack_legend_object,
    is_valid_hex,
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
        border_show, border_color, border_radius, border_width = unpack_border_object(style_obj)
        if border_show:
            generic["border"] = {"color": border_color, "radius": border_radius, "width": border_width}

    if "dropShadow" in style_obj:
        shadow_show, shadow_color = unpack_drop_shadow_object(style_obj)
        if shadow_show:
            generic["dropShadow"] = {"color": shadow_color}

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

    if "visualHeader" in style_obj:
        vh_show, vh_bg, vh_fg = unpack_visual_header_object(style_obj)
        if vh_show:
            generic["visualHeader"] = {"background": vh_bg, "foreground": vh_fg}

    if "padding" in style_obj:
        generic["padding"] = unpack_padding_object(style_obj)

    if "subTitle" in style_obj:
        sub_show, sub_text, sub_color, sub_size = unpack_subtitle_object(style_obj)
        if sub_show:
            generic["subtitle"] = {"text": sub_text, "color": sub_color, "size": sub_size}

    if "divider" in style_obj:
        div_show, div_color, div_width, div_style = unpack_divider_object(style_obj)
        if div_show:
            generic["divider"] = {"color": div_color, "width": div_width, "style": div_style}

    return generic


def _frame(width: int, height: int, generic: Dict[str, Any], theme_bg: str) -> List[str]:
    """Background rect (+ optional generic background/border) for any mockup."""
    generic = generic or {}
    parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    gborder = generic.get("border")
    radius = int(gborder.get("radius", 0)) if gborder else 0
    rx = f' rx="{radius}"' if radius else ""

    # Drop shadow: an offset rounded rect behind the visual.
    gshadow = generic.get("dropShadow")
    if gshadow:
        parts.append(
            f'<rect x="4" y="4" width="{width - 6}" height="{height - 6}"{rx} '
            f'fill="{gshadow["color"]}" opacity="0.35"/>'
        )

    gbg = generic.get("background")
    if gbg:
        opacity = max(0.0, min(1.0, gbg.get("transparency", 100) / 100.0))
        parts.append(f'<rect width="{width}" height="{height}"{rx} fill="{gbg["color"]}" opacity="{opacity:.2f}"/>')
    else:
        parts.append(f'<rect width="{width}" height="{height}"{rx} fill="{theme_bg}"/>')

    if gborder:
        w = int(gborder.get("width", 1)) or 1
        off = w / 2 + 0.5
        parts.append(
            f'<rect x="{off:.1f}" y="{off:.1f}" width="{width - off * 2:.1f}" height="{height - off * 2:.1f}"{rx} '
            f'fill="none" stroke="{gborder["color"]}" stroke-width="{w}"/>'
        )

    # Padding guide: a faint dashed inset showing the content area.
    pad = generic.get("padding")
    if pad:
        parts.append(
            f'<rect x="{pad}" y="{pad}" width="{width - pad * 2}" height="{height - pad * 2}" '
            f'fill="none" stroke="#B3B0AD" stroke-width="1" stroke-dasharray="3,3" opacity="0.7"/>'
        )

    # Visual header: a strip with icon dots at the top-right of the container.
    vh = generic.get("visualHeader")
    if vh:
        parts.append(f'<rect x="0" y="0" width="{width}" height="12" fill="{vh["background"]}" opacity="0.9"/>')
        for i in range(3):
            parts.append(f'<circle cx="{width - 10 - i * 10}" cy="6" r="2" fill="{vh["foreground"]}"/>')
    return parts


def _title(width: int, default_text: str, default_color: str,
           generic: Dict[str, Any]) -> Tuple[str, int]:
    """Return (title <text> svg, y-offset consumed) honoring a generic title override."""
    generic = generic or {}
    gtitle = generic.get("title")
    color = gtitle["color"] if gtitle else default_color
    size = int(gtitle["size"]) if gtitle else 13
    y = size + 4
    svg = (
        f'<text x="{width // 2}" y="{y}" font-size="{size}" fill="{color}" '
        f'text-anchor="middle" font-weight="bold">{_esc(default_text)}</text>'
    )
    consumed = y + 4
    # A subtitle renders just below the title.
    gsub = generic.get("subtitle")
    if gsub:
        sub_size = int(gsub.get("size", 10))
        sub_text = gsub.get("text") or "Subtitle"
        sub_y = consumed + sub_size
        svg += (
            f'<text x="{width // 2}" y="{sub_y}" font-size="{sub_size}" fill="{gsub["color"]}" '
            f'text-anchor="middle">{_esc(sub_text)}</text>'
        )
        consumed = sub_y + 4
    # A divider separating the title area from the content.
    gdiv = generic.get("divider")
    if gdiv:
        dw = int(gdiv.get("width", 1)) or 1
        dash = {"dashed": ' stroke-dasharray="6,3"', "dotted": ' stroke-dasharray="1,3"'}.get(
            gdiv.get("style", "solid"), "")
        dy = consumed + dw
        svg += (
            f'<line x1="6" y1="{dy:.1f}" x2="{width - 6}" y2="{dy:.1f}" '
            f'stroke="{gdiv["color"]}" stroke-width="{dw}"{dash}/>'
        )
        consumed = dy + dw + 3
    return svg, consumed


def _font_attrs(formatting: Dict[str, Any], bold_key: str, italic_key: str) -> str:
    """Return the bold / italic SVG text attributes for a card's font styling."""
    attrs = ""
    if _flag(formatting, bold_key, False):
        attrs += ' font-weight="bold"'
    if _flag(formatting, italic_key, False):
        attrs += ' font-style="italic"'
    return attrs


def _legend(x: int, y: int, colors: List[str], formatting: Dict[str, Any],
            generic: Dict[str, Any], horizontal: bool) -> List[str]:
    """Render a small 3-series legend at (x, y)."""
    gleg = (generic or {}).get("legend")
    color = gleg["color"] if gleg else _col(formatting, "legendTextColor", "#252423")
    size = int(_num(formatting, "legendFontSize", 10))
    fa = _font_attrs(formatting, "legendBold", "legendItalic")
    names = ["Series A", "Series B", "Series C"]
    parts: List[str] = []
    cx, cy = x, y
    if _flag(formatting, "legendShowTitle", False):
        title = _txt(formatting, "legendTitleText", "Legend")
        title_italic = ' font-style="italic"' if _flag(formatting, "legendItalic", False) else ""
        parts.append(f'<text x="{cx}" y="{cy}" font-size="{size}" fill="{color}" font-weight="bold"{title_italic}>{_esc(title)}</text>')
        if horizontal:
            cx += size + 6 + len(title) * size * 0.55
        else:
            cy += size + 6
    for i, name in enumerate(names[: len(colors)]):
        parts.append(f'<rect x="{cx}" y="{cy - size + 2}" width="{size}" height="{size}" fill="{colors[i]}"/>')
        parts.append(
            f'<text x="{cx + size + 3}" y="{cy}" font-size="{size}" fill="{color}"{fa}>{name}</text>'
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


def _series_colors(theme: PowerBITheme, n: int = 3,
                   formatting: Dict[str, Any] | None = None) -> List[str]:
    colors = list(theme.data_colors[:n]) if theme.data_colors else []
    if not colors:
        colors = [theme.table_accent]
    while len(colors) < n:
        colors.append(colors[-1])
    # A per-visual default data-point colour overrides the primary series.
    default = _col(formatting, "defaultColor", "") if formatting else ""
    if default and is_valid_hex(default):
        colors[0] = default
    return colors


_UNIT_SUFFIX = {1000: "K", 1000000: "M", 1000000000: "bn", 1000000000000: "tn"}


def _format_measure(value: float, formatting: Dict[str, Any]) -> str:
    """Format a numeric data-label value with display units and decimal precision."""
    units = int(_num(formatting, "dataLabelDisplayUnits", 1) or 1)
    prec = int(_num(formatting, "dataLabelPrecision", 0))
    if units > 1:
        return f"{value / units:.{prec}f}{_UNIT_SUFFIX.get(units, '')}"
    return f"{value:.{prec}f}" if prec > 0 else f"{int(round(value))}"


def _data_label(x: float, y: float, text: Any, formatting: Dict[str, Any],
                generic: Dict[str, Any], with_bg: bool = False) -> List[str]:
    """A single chart data label honoring generic labels or the chart dataLabel fields."""
    color = generic["labels"]["color"] if (generic or {}).get("labels") else _col(formatting, "dataLabelColor", "#252423")
    size = int(generic["labels"]["size"]) if (generic or {}).get("labels") else int(_num(formatting, "dataLabelFontSize", 8))
    with_bg = with_bg or _flag(formatting, "dataLabelBackground", False)
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        text = _format_measure(text, formatting)
    # A non-default label position nudges the label relative to the mark.
    y += {"OutsideEnd": -4, "InsideEnd": size + 3, "InsideCenter": size + 12,
          "InsideBase": size + 22, "Under": size + 6}.get(_txt(formatting, "dataLabelPosition", "Auto"), 0)
    parts: List[str] = []
    if with_bg:
        parts.append(
            f'<rect x="{x - 9:.1f}" y="{y - size:.1f}" width="18" height="{size + 3}" fill="#FFFFFF" opacity="0.7"/>'
        )
    fa = _font_attrs(formatting, "dataLabelBold", "dataLabelItalic")
    parts.append(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="middle"{fa}>{_esc(text)}</text>'
    )
    return parts


def _labels_on(formatting: Dict[str, Any], generic: Dict[str, Any]) -> bool:
    return bool((generic or {}).get("labels")) or bool((formatting or {}).get("dataLabelColor"))


def _pt(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
    """Point on a circle; 0 deg = right, 90 = top (screen y is flipped)."""
    a = math.radians(deg)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def _wedge(cx: float, cy: float, r: float, start: float, end: float, color: str,
           inner: float = 0.0) -> str:
    """Pie/donut wedge path from start->end degrees (counter-clockwise)."""
    large = 1 if (end - start) % 360 > 180 else 0
    x1, y1 = _pt(cx, cy, r, start)
    x2, y2 = _pt(cx, cy, r, end)
    if inner <= 0:
        return (f'<path d="M{cx:.1f},{cy:.1f} L{x1:.1f},{y1:.1f} '
                f'A{r:.1f},{r:.1f} 0 {large} 0 {x2:.1f},{y2:.1f} Z" fill="{color}"/>')
    ix1, iy1 = _pt(cx, cy, inner, start)
    ix2, iy2 = _pt(cx, cy, inner, end)
    return (f'<path d="M{x1:.1f},{y1:.1f} A{r:.1f},{r:.1f} 0 {large} 0 {x2:.1f},{y2:.1f} '
            f'L{ix2:.1f},{iy2:.1f} A{inner:.1f},{inner:.1f} 0 {large} 1 {ix1:.1f},{iy1:.1f} Z" fill="{color}"/>')


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
    colors = _series_colors(theme, 3, formatting)

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

    def _tick(v):
        return f"{v:.0f}" if float(v).is_integer() else f"{v:.1f}"

    if _flag(formatting, "yAxisSetRange", False):
        # A fixed range relabels the ticks to start / mid / end and caps the axis.
        rs = _num(formatting, "yAxisStart", 0)
        re = _num(formatting, "yAxisEnd", 100)
        y_ticks = ((0.0, _tick(rs)), (0.5, _tick((rs + re) / 2)), (1.0, _tick(re)))
        for cap_y in (plot_t, plot_b):
            parts.append(f'<line x1="{plot_l - 3}" y1="{cap_y:.1f}" x2="{plot_l + 3}" y2="{cap_y:.1f}" stroke="{fg}" stroke-width="1.5"/>')
    elif _flag(formatting, "yAxisLogScale", False):
        # A log scale relabels the ticks (1 / 10 / 100).
        y_ticks = ((0.0, "1"), (0.5, "10"), (1.0, "100"))
    else:
        y_ticks = ((0.0, "0"), (0.5, "50"), (1.0, "100"))
    if _flag(formatting, "yAxisLogScale", False):
        # Faint minor gridlines mark the compressed log decades (shown regardless of range).
        for frac in (0.15, 0.30, 0.70, 0.85):
            gy = plot_b - frac * (plot_b - plot_t)
            parts.append(f'<line x1="{plot_l}" y1="{gy:.1f}" x2="{plot_r}" y2="{gy:.1f}" stroke="{fg}" stroke-width="0.4" stroke-dasharray="1,2" opacity="0.4"/>')
    y_fa = _font_attrs(formatting, "yAxisBold", "yAxisItalic")
    for frac, val in y_ticks:
        gy = plot_b - frac * (plot_b - plot_t)
        parts.append(
            f'<text x="{plot_l - 4}" y="{gy + y_lab_size / 3:.1f}" font-size="{y_lab_size}" '
            f'fill="{y_lab_color}" text-anchor="end"{y_fa}>{val}</text>'
        )
    y_title_color = _col(formatting, "yAxisTitleColor", fg)
    y_title_size = int(_num(formatting, "yAxisTitleFontSize", 8))
    y_title = _txt(formatting, "yAxisTitleText", "Value")
    ty = (plot_t + plot_b) / 2
    parts.append(
        f'<text x="10" y="{ty:.1f}" font-size="{y_title_size}" fill="{y_title_color}" '
        f'text-anchor="middle" transform="rotate(-90 10 {ty:.1f})">{_esc(y_title)}</text>'
    )

    # ---- X-axis labels + title ---- #
    x_lab_color = _col(formatting, "xAxisLabelColor", fg)
    x_lab_size = int(_num(formatting, "xAxisLabelFontSize", 8))
    x_fa = _font_attrs(formatting, "xAxisBold", "xAxisItalic")
    cats = ["Q1", "Q2", "Q3", "Q4"]
    span = (plot_r - plot_l) / len(cats)
    for i, cat in enumerate(cats):
        cx = plot_l + span * (i + 0.5)
        parts.append(
            f'<text x="{cx:.1f}" y="{plot_b + x_lab_size + 4}" font-size="{x_lab_size}" '
            f'fill="{x_lab_color}" text-anchor="middle"{x_fa}>{cat}</text>'
        )
    x_title_color = _col(formatting, "xAxisTitleColor", fg)
    x_title_size = int(_num(formatting, "xAxisTitleFontSize", 8))
    x_title = _txt(formatting, "xAxisTitleText", "Category")
    parts.append(
        f'<text x="{(plot_l + plot_r) / 2:.1f}" y="{height - 4}" font-size="{x_title_size}" '
        f'fill="{x_title_color}" text-anchor="middle">{_esc(x_title)}</text>'
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

    # Reference line (horizontal at a value) and trend line (diagonal).
    if _flag(formatting, "refLineShow", False):
        rv = max(0.0, min(1.0, _num(formatting, "refLineValue", 50) / 100.0))
        ry = plot_b - rv * (plot_b - plot_t)
        parts.append(f'<line x1="{plot_l}" y1="{ry:.1f}" x2="{plot_r}" y2="{ry:.1f}" '
                     f'stroke="{_col(formatting, "refLineColor", "#E66C37")}" stroke-width="1.5" stroke-dasharray="5,3"/>')
    if _flag(formatting, "trendShow", False):
        span = plot_b - plot_t
        parts.append(f'<line x1="{plot_l}" y1="{plot_b - 0.25 * span:.1f}" x2="{plot_r}" y2="{plot_b - 0.8 * span:.1f}" '
                     f'stroke="{_col(formatting, "trendColor", "#605E5C")}" stroke-width="2" stroke-dasharray="4,3"/>')

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
    colors = _series_colors(theme, 3, formatting)

    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Bar Chart")

    groups = [[70, 55, 40], [85, 65, 50], [65, 75, 60], [90, 80, 70]]
    span = (pr - pl) / len(groups)
    bar_w = span / 4.2
    scale = (pb - pt) / 100.0

    show_labels = _labels_on(formatting, generic)

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
            parts += _data_label(lx, ly, top_val, formatting, generic)

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
    colors = _series_colors(theme, 3, formatting)

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
                parts += _data_label(x, y, val, formatting, generic)

    parts.append("</svg>")
    return "\n".join(parts)


def generate_area_chart_svg(theme, formatting=None, generic=None, width=300, height=200,
                            label="Area Chart", stacked=False, percent=False):
    """Area chart: overlapping filled areas, or stacked / 100%-stacked bands."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 3, formatting)
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, label)
    series = [[40, 55, 50, 70, 65, 80], [30, 40, 45, 55, 60, 68], [20, 28, 35, 42, 48, 58]]
    scale = (pb - pt) / 100.0
    full = pb - pt
    n = len(series[0])
    step = (pr - pl) / (n - 1)

    if stacked:
        col_tot = [sum(series[s][i] for s in range(len(series))) for i in range(n)]
        cum = [0.0] * n
        top_pts = None
        for si in range(len(series)):
            lower, upper = [], []
            for i in range(n):
                base, top = cum[i], cum[i] + series[si][i]
                if percent:
                    ly = pb - full * (base / col_tot[i])
                    uy = pb - full * (top / col_tot[i])
                else:
                    ly, uy = pb - base * scale, pb - top * scale
                lower.append((pl + i * step, ly))
                upper.append((pl + i * step, uy))
                cum[i] = top
            band = (" ".join(f"{x:.1f},{y:.1f}" for x, y in upper) + " "
                    + " ".join(f"{x:.1f},{y:.1f}" for x, y in reversed(lower)))
            parts.append(f'<polygon points="{band}" fill="{colors[si]}" opacity="0.8"/>')
            parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in upper)}" '
                         f'fill="none" stroke="{colors[si]}" stroke-width="1.5"/>')
            top_pts = upper
        if _labels_on(formatting, generic) and top_pts:
            for i, (x, y) in enumerate(top_pts):
                val = 100.0 if percent else col_tot[i]
                parts += _data_label(x, y - 3, val, formatting, generic)
    else:
        for si in reversed(range(len(series))):  # back-to-front so fills overlap nicely
            pts = [(pl + i * step, pb - v * scale) for i, v in enumerate(series[si])]
            poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            area = f"{pl:.1f},{pb:.1f} " + poly + f" {pr:.1f},{pb:.1f}"
            parts.append(f'<polygon points="{area}" fill="{colors[si]}" opacity="0.35"/>')
            parts.append(f'<polyline points="{poly}" fill="none" stroke="{colors[si]}" stroke-width="2"/>')
        if _labels_on(formatting, generic):
            for i, v in enumerate(series[0]):
                parts += _data_label(pl + i * step, pb - v * scale - 3, v, formatting, generic)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_combo_chart_svg(theme, formatting=None, generic=None, width=300, height=200,
                             stacked=False):
    """Line & column combo: grouped/stacked columns plus a line overlay."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 3, formatting)
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Line & Column")
    cols = [[55, 35], [70, 45], [50, 60], [80, 55]]  # two column series per category
    line_vals = [70, 85, 78, 95]
    span = (pr - pl) / len(cols)
    scale = (pb - pt) / 120.0
    bw = span * (0.5 if not stacked else 0.35)
    for gi, pair in enumerate(cols):
        cx = pl + span * gi + span * 0.2
        if stacked:
            y0 = pb
            for si, v in enumerate(pair):
                h = v * scale
                parts.append(f'<rect x="{cx:.1f}" y="{y0 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{colors[si]}" opacity="0.9"/>')
                y0 -= h
        else:
            for si, v in enumerate(pair):
                h = v * scale
                parts.append(f'<rect x="{cx + si * bw / 2:.1f}" y="{pb - h:.1f}" width="{bw / 2:.1f}" height="{h:.1f}" fill="{colors[si]}" opacity="0.9"/>')
    lpts = " ".join(f"{pl + span * (i + 0.5):.1f},{pb - v * scale:.1f}" for i, v in enumerate(line_vals))
    parts.append(f'<polyline points="{lpts}" fill="none" stroke="{colors[2]}" stroke-width="2.5"/>')
    if _labels_on(formatting, generic):
        for i, v in enumerate(line_vals):
            parts += _data_label(pl + span * (i + 0.5), pb - v * scale - 3, v, formatting, generic)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_stacked_chart_svg(theme, formatting=None, generic=None, width=300, height=200,
                               percent=True):
    """100% stacked columns: one full-height bar per category split into segments."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 3, formatting)
    title = "100% Stacked" if percent else "Stacked"
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, title)
    groups = [[40, 35, 25], [30, 45, 25], [50, 20, 30], [35, 40, 25]]
    span = (pr - pl) / len(groups)
    bw = span * 0.55
    full = pb - pt
    for gi, vals in enumerate(groups):
        total = sum(vals) if percent else 100
        x = pl + span * gi + (span - bw) / 2
        y0 = pb
        for si, v in enumerate(vals):
            h = full * (v / total)
            parts.append(f'<rect x="{x:.1f}" y="{y0 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{colors[si]}" opacity="0.9"/>')
            if _labels_on(formatting, generic):
                parts += _data_label(x + bw / 2, y0 - h / 2 + 3, 100.0 * v / total, formatting, generic)
            y0 -= h
    parts.append("</svg>")
    return "\n".join(parts)


def generate_scatter_chart_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Scatter plot: points across the X/Y plane, coloured by series."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 3, formatting)
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Scatter Chart")
    pts_by_series = [
        [(0.15, 0.30), (0.30, 0.55), (0.45, 0.40), (0.60, 0.70), (0.80, 0.62)],
        [(0.20, 0.65), (0.38, 0.35), (0.55, 0.52), (0.70, 0.30), (0.88, 0.45)],
        [(0.25, 0.20), (0.50, 0.80), (0.65, 0.60), (0.82, 0.78), (0.35, 0.72)],
    ]
    labels_on = _labels_on(formatting, generic)
    radius = 2 + _num(formatting, "bubbleSize", 20) * 0.12
    border = _col(formatting, "markerBorderColor", "#FFFFFF")
    for si, pts in enumerate(pts_by_series):
        for fx, fy in pts:
            cx = pl + fx * (pr - pl)
            cy = pb - fy * (pb - pt)
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="{colors[si]}" opacity="0.85" stroke="{border}" stroke-width="1"/>')
            if labels_on and si == 0:
                parts += _data_label(cx, cy - radius - 3, round(fy * 100), formatting, generic)
    # Ratio line: a diagonal from bottom-left to top-right of the plot.
    if _flag(formatting, "ratioLineShow", False):
        rl_col = _col(formatting, "ratioLineColor", "#605E5C")
        parts.append(
            f'<line x1="{pl:.1f}" y1="{pb:.1f}" x2="{pr:.1f}" y2="{pt:.1f}" '
            f'stroke="{rl_col}" stroke-width="1.5" stroke-dasharray="5,3"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def generate_waterfall_chart_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Waterfall: floating step bars (increase / decrease / total) with connectors."""
    formatting, generic = formatting or {}, generic or {}
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Waterfall")
    inc_color = _col(formatting, "defaultColor", theme.good)
    dec_color = _col(formatting, "decreaseColor", theme.bad)
    tot_color = _col(formatting, "totalColor", theme.table_accent)
    steps = [("start", 40), ("inc", 25), ("dec", -15), ("inc", 20), ("total", None)]
    span = (pr - pl) / len(steps)
    bw = span * 0.55
    scale = (pb - pt) / 100.0
    running = 0
    prev_top = None
    for i, (kind, delta) in enumerate(steps):
        x = pl + span * i + (span - bw) / 2
        if kind == "total":
            bottom, top = pb, pb - running * scale
            color = tot_color
        else:
            start = running
            running += delta
            lo, hi = min(start, running), max(start, running)
            bottom, top = pb - lo * scale, pb - hi * scale
            color = inc_color if (kind == "inc" or kind == "start") else dec_color
        parts.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(1, bottom - top):.1f}" fill="{color}" opacity="0.9"/>')
        if prev_top is not None:
            parts.append(f'<line x1="{x - (span - bw):.1f}" y1="{prev_top:.1f}" x2="{x:.1f}" y2="{prev_top:.1f}" stroke="{theme.foreground}" stroke-width="0.7" stroke-dasharray="2,2"/>')
        if _labels_on(formatting, generic):
            val = round(running) if kind != "total" else round(running)
            parts += _data_label(x + bw / 2, top - 3, val, formatting, generic)
        prev_top = top
    parts.append("</svg>")
    return "\n".join(parts)


def generate_ribbon_chart_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Ribbon: stacked columns per category with ribbons connecting categories."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 3, formatting)
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Ribbon Chart")
    groups = [[40, 30, 25], [25, 45, 30], [35, 25, 40], [30, 40, 30]]
    span = (pr - pl) / len(groups)
    bw = span * 0.5
    full = pb - pt
    tops = []  # per group: list of (series, y_top, y_bottom)
    for gi, vals in enumerate(groups):
        total = sum(vals)
        x = pl + span * gi + (span - bw) / 2
        y0 = pb
        seg = {}
        for si, v in enumerate(vals):
            h = full * (v / total)
            parts.append(f'<rect x="{x:.1f}" y="{y0 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{colors[si]}" opacity="0.95"/>')
            if _labels_on(formatting, generic) and si == 0:
                parts += _data_label(x + bw / 2, y0 - h / 2 + 3, v, formatting, generic)
            seg[si] = (x, y0 - h, y0)
            y0 -= h
        tops.append(seg)
    # ribbons between adjacent categories
    for gi in range(len(groups) - 1):
        for si in range(3):
            x1, t1, b1 = tops[gi][si]
            x2, t2, b2 = tops[gi + 1][si]
            rx1, rx2 = x1 + bw, x2
            parts.append(
                f'<path d="M{rx1:.1f},{t1:.1f} C{(rx1 + rx2) / 2:.1f},{t1:.1f} {(rx1 + rx2) / 2:.1f},{t2:.1f} {rx2:.1f},{t2:.1f} '
                f'L{rx2:.1f},{b2:.1f} C{(rx1 + rx2) / 2:.1f},{b2:.1f} {(rx1 + rx2) / 2:.1f},{b1:.1f} {rx1:.1f},{b1:.1f} Z" '
                f'fill="{colors[si]}" opacity="0.30"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def generate_pie_chart_svg(theme, formatting=None, generic=None, width=300, height=200,
                           donut=False):
    """Pie / donut with wedges, slice labels and a legend (no cartesian axes)."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 4)
    vals = [35, 25, 22, 18]
    title_text = "Donut Chart" if donut else "Pie Chart"
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, title_text, theme.foreground, generic)

    legend_pos = _legend_position(formatting, generic)
    cx = width * (0.42 if legend_pos == "Right" else 0.58 if legend_pos == "Left" else 0.5)
    cy = top + (height - top) * 0.52
    r = min(width, height - top) * 0.36
    inner_pct = _num(formatting, "sliceInnerRadius", 0)
    inner = r * (inner_pct / 100.0) if inner_pct > 0 else (r * 0.55 if donut else 0.0)

    total = sum(vals)
    show_labels = _flag(formatting, "showDataLabels", True)
    dl_color = _col(formatting, "dataLabelColor", "#FFFFFF")
    dl_size = int(_num(formatting, "dataLabelFontSize", 9))
    dl_fa = _font_attrs(formatting, "dataLabelBold", "dataLabelItalic")
    angle = 90.0 - _num(formatting, "sliceStartAngle", 0)  # start at top, offset by start angle
    for i, v in enumerate(vals):
        sweep = 360.0 * v / total
        parts.append(_wedge(cx, cy, r, angle, angle + sweep, colors[i], inner))
        if show_labels:
            mid = angle + sweep / 2
            lx, ly = _pt(cx, cy, (r + inner) / 2 if donut else r * 0.62, mid)
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + dl_size / 3:.1f}" font-size="{dl_size}" fill="{dl_color}" '
                f'text-anchor="middle"{dl_fa}>{round(100 * v / total)}%</text>'
            )
        angle += sweep

    if legend_pos == "Top":
        parts += _legend(int(width * 0.35), top + 12, colors, formatting, generic, horizontal=True)
    elif legend_pos == "Bottom":
        parts += _legend(int(width * 0.35), height - 10, colors, formatting, generic, horizontal=True)
    elif legend_pos == "Left":
        parts += _legend(6, top + 20, colors, formatting, generic, horizontal=False)
    else:  # Right
        parts += _legend(int(width - 70), top + 20, colors, formatting, generic, horizontal=False)

    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_gauge_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Radial gauge: value arc, target tick, min/max scale and callout value."""
    formatting, generic = formatting or {}, generic or {}
    fg = theme.foreground
    vmin = _num(formatting, "minValue", 0)
    vmax = _num(formatting, "maxValue", 100)
    if vmax <= vmin:
        vmax = vmin + 1
    value = vmin + (vmax - vmin) * 0.68
    target = _num(formatting, "targetValue", vmin + (vmax - vmin) * 0.85)
    fill = _col(formatting, "fillColor", theme.table_accent)
    target_col = _col(formatting, "targetColor", "#E66C37")

    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Gauge", fg, generic)

    cx, cy = width / 2, top + (height - top) * 0.72
    r = min(width * 0.36, (height - top) * 0.62)
    thick = max(10, r * 0.28)

    def frac_to_deg(f):
        return 180 - 180 * f  # 180deg (left) -> 0deg (right)

    # Track (background arc) then value arc. Sampled as a polyline so the shape
    # and direction are always correct regardless of span (arc-flags are fiddly
    # near 180deg, and a gauge span is never more than 180deg anyway).
    def arc(f_start, f_end, color, w):
        n = max(2, int(48 * abs(f_end - f_start)))
        pts = []
        for i in range(n + 1):
            f = f_start + (f_end - f_start) * (i / n)
            x, y = _pt(cx, cy, r, frac_to_deg(f))
            pts.append(f"{x:.1f},{y:.1f}")
        return (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
                f'stroke-width="{w:.1f}" stroke-linecap="round"/>')

    parts.append(arc(0.0, 1.0, "#E0E0E0", thick))
    vfrac = max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    if vfrac > 0:
        parts.append(arc(0.0, vfrac, fill, thick))

    # Target tick
    tfrac = max(0.0, min(1.0, (target - vmin) / (vmax - vmin)))
    tx1, ty1 = _pt(cx, cy, r - thick / 2, frac_to_deg(tfrac))
    tx2, ty2 = _pt(cx, cy, r + thick / 2, frac_to_deg(tfrac))
    parts.append(f'<line x1="{tx1:.1f}" y1="{ty1:.1f}" x2="{tx2:.1f}" y2="{ty2:.1f}" stroke="{target_col}" stroke-width="3"/>')

    # Min / max labels
    parts.append(f'<text x="{cx - r:.1f}" y="{cy + 14:.1f}" font-size="9" fill="{fg}" text-anchor="middle">{round(vmin)}</text>')
    parts.append(f'<text x="{cx + r:.1f}" y="{cy + 14:.1f}" font-size="9" fill="{fg}" text-anchor="middle">{round(vmax)}</text>')

    # Callout value
    if _flag(formatting, "showCallout", True):
        c_color = _col(formatting, "calloutColor", "#252423")
        c_size = int(_num(formatting, "calloutFontSize", 24))
        parts.append(
            f'<text x="{cx:.1f}" y="{cy - 4:.1f}" font-size="{c_size}" fill="{c_color}" '
            f'text-anchor="middle" font-weight="bold">{round(value)}</text>'
        )
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_treemap_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Treemap: proportional coloured rectangles with category labels + legend."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 5)
    cats = [("A", 40), ("B", 24), ("C", 18), ("D", 10), ("E", 8)]
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Treemap", theme.foreground, generic)

    legend_pos = _legend_position(formatting, generic)
    area_l, area_t = 8, top + 4
    area_r, area_b = width - 8, height - 8
    if legend_pos == "Bottom":
        area_b -= 16
    elif legend_pos == "Top":
        area_t += 16
    elif legend_pos == "Left":
        area_l += 66
    elif legend_pos == "Right":
        area_r -= 66

    show_labels = _flag(formatting, "showDataLabels", True)
    dl_color = _col(formatting, "dataLabelColor", "#FFFFFF")
    dl_size = int(_num(formatting, "dataLabelFontSize", 9))
    dl_fa = _font_attrs(formatting, "dataLabelBold", "dataLabelItalic")

    # Simple slice-and-dice: big box left, remainder stacked on the right.
    total = sum(v for _, v in cats)
    x = area_l
    remaining = cats[:]
    W, H = area_r - area_l, area_b - area_t
    # First (largest) takes a left column proportional to its share.
    first_label, first_val = remaining.pop(0)
    fw = W * (first_val / total)
    boxes = [(x, area_t, fw, H, first_label, colors[0])]
    x += fw
    rest_total = sum(v for _, v in remaining) or 1
    y = area_t
    for i, (lab, v) in enumerate(remaining):
        bh = H * (v / rest_total)
        boxes.append((x, y, W - fw, bh, lab, colors[(i + 1) % len(colors)]))
        y += bh
    for bx, by, bw, bh, lab, color in boxes:
        parts.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{color}" stroke="#FFFFFF" stroke-width="1.5"/>')
        if show_labels and bw > 16 and bh > 12:
            parts.append(
                f'<text x="{bx + 5:.1f}" y="{by + dl_size + 3:.1f}" font-size="{dl_size}" fill="{dl_color}"{dl_fa}>{_esc(lab)}</text>'
            )

    if legend_pos in ("Top", "Bottom"):
        ly = (top + 12) if legend_pos == "Top" else (height - 6)
        parts += _legend(area_l, ly, colors[:3], formatting, generic, horizontal=True)
    elif legend_pos == "Left":
        parts += _legend(6, area_t + 12, colors[:4], formatting, generic, horizontal=False)
    else:
        parts += _legend(int(width - 62), area_t + 12, colors[:4], formatting, generic, horizontal=False)

    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_funnel_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Funnel: centred, decreasing horizontal bars with stage labels."""
    formatting, generic = formatting or {}, generic or {}
    stages = [("Leads", 100), ("Qualified", 72), ("Proposal", 48), ("Won", 30)]
    bar_color = _col(formatting, "barColor", theme.table_accent)
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Funnel", theme.foreground, generic)

    show_labels = _flag(formatting, "showDataLabels", True)
    dl_color = _col(formatting, "dataLabelColor", "#FFFFFF")
    dl_size = int(_num(formatting, "dataLabelFontSize", 9))
    dl_fa = _font_attrs(formatting, "dataLabelBold", "dataLabelItalic")

    max_w = width * 0.8
    cx = width / 2
    avail = height - top - 12
    bh = avail / len(stages) * 0.7
    gap = avail / len(stages) * 0.3
    y = top + 6
    for label, v in stages:
        bw = max_w * (v / 100.0)
        parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{bar_color}" opacity="0.9"/>')
        if show_labels:
            parts.append(
                f'<text x="{cx:.1f}" y="{y + bh / 2 + dl_size / 3:.1f}" font-size="{dl_size}" fill="{dl_color}" '
                f'text-anchor="middle"{dl_fa}>{_esc(label)}: {v}</text>'
            )
        y += bh + gap
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_multirow_card_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Multi-row card: several label/value rows honoring card formatting."""
    formatting, generic = formatting or {}, generic or {}
    fg = theme.foreground
    value_color = _col(formatting, "valueColor", theme.good)
    value_size = int(_num(formatting, "valueFontSize", 20))
    value_bold = _flag(formatting, "valueFontBold", True)
    label_color = _col(formatting, "labelColor", fg)
    label_size = int(_num(formatting, "labelFontSize", 11))
    card_bg = _col(formatting, "backgroundColor", "#FFFFFF")
    show_border = _flag(formatting, "backgroundBorder", False)

    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Multi-row Card", fg, generic)

    rows = [("Revenue", "$1.2M"), ("Orders", "8,540"), ("Avg. Value", "$141")]
    pad = 12
    rh = (height - top - pad) / len(rows)
    y = top + 4
    stroke = f' stroke="{fg}" stroke-width="1"' if show_border else ""
    for label, val in rows:
        parts.append(f'<rect x="{pad}" y="{y:.1f}" width="{width - pad * 2}" height="{rh - 6:.1f}" rx="3" fill="{card_bg}"{stroke}/>')
        parts.append(f'<text x="{pad + 10}" y="{y + label_size + 4:.1f}" font-size="{label_size}" fill="{label_color}">{_esc(label)}</text>')
        weight = "bold" if value_bold else "normal"
        parts.append(f'<text x="{pad + 10}" y="{y + rh - 12:.1f}" font-size="{value_size}" fill="{value_color}" font-weight="{weight}">{_esc(val)}</text>')
        y += rh
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_kpi_svg(theme, formatting=None, generic=None, width=300, height=200):
    """KPI: a large indicator value, a goal line, a trend line and a status arrow."""
    formatting, generic = formatting or {}, generic or {}
    fg = theme.foreground

    ind_color = _col(formatting, "indicatorFontColor", fg)
    ind_size = int(_num(formatting, "indicatorFontSize", 40))
    ind_bold = _flag(formatting, "indicatorBold", True)
    show_goal = _flag(formatting, "showGoal", True)
    goal_color = _col(formatting, "goalFontColor", "#605E5C")
    goal_size = int(_num(formatting, "goalFontSize", 12))
    trend_show = _flag(formatting, "trendlineShow", True)
    good = _col(formatting, "statusGoodColor", theme.good)
    bad = _col(formatting, "statusBadColor", theme.bad)

    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "KPI", fg, generic)

    cx = width // 2
    # Trend line across the lower third (in the good colour), with a bad dip.
    if trend_show:
        ty = top + (height - top) * 0.72
        pts = [(0.08, 0.0), (0.28, -12), (0.5, -6), (0.7, -20), (0.92, -28)]
        poly = " ".join(f"{0.0 + fx * width:.1f},{ty + dy:.1f}" for fx, dy in pts)
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{good}" stroke-width="2.5" opacity="0.85"/>')
        parts.append(f'<circle cx="{0.7 * width:.1f}" cy="{ty - 20:.1f}" r="3" fill="{bad}"/>')

    weight = "bold" if ind_bold else "normal"
    vy = top + (height - top) * 0.42
    parts.append(
        f'<text x="{cx}" y="{vy:.0f}" font-size="{ind_size}" fill="{ind_color}" '
        f'text-anchor="middle" font-weight="{weight}">$1.2M</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{vy + ind_size * 0.55:.0f}" font-size="12" fill="{good}" '
        f'text-anchor="middle">▲ +12.5%</text>'
    )
    if show_goal:
        parts.append(
            f'<text x="{cx}" y="{vy + ind_size * 0.55 + goal_size + 6:.0f}" font-size="{goal_size}" '
            f'fill="{goal_color}" text-anchor="middle">Goal: $1.5M (80%)</text>'
        )

    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_slicer_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Slicer: a header plus a short list of selectable items."""
    formatting, generic = formatting or {}, generic or {}
    fg = theme.foreground
    accent = theme.table_accent

    header_show = _flag(formatting, "headerShow", True)
    header_fg = _col(formatting, "headerFontColor", fg)
    header_bg = _col(formatting, "headerBackground", "#FFFFFF")
    header_size = int(_num(formatting, "headerTextSize", 12))
    header_bold = _flag(formatting, "headerBold", False)

    item_fg = _col(formatting, "itemsFontColor", fg)
    item_bg = _col(formatting, "itemsBackground", "#FFFFFF")
    item_size = int(_num(formatting, "itemsTextSize", 11))
    item_bold = _flag(formatting, "itemsBold", False)
    select_col = _col(formatting, "selectionColor", accent)

    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Slicer", fg, generic)

    pad = 10
    y = top + 4
    if header_show:
        hh = header_size + 12
        parts.append(f'<rect x="{pad}" y="{y:.1f}" width="{width - pad * 2}" height="{hh}" fill="{header_bg}" stroke="#DDDDDD" stroke-width="1"/>')
        weight = "bold" if header_bold else "normal"
        parts.append(
            f'<text x="{pad + 8}" y="{y + header_size + 2:.1f}" font-size="{header_size}" fill="{header_fg}" '
            f'font-weight="{weight}">Category</text>'
        )
        y += hh + 4

    items = [("Alpha", True), ("Bravo", False), ("Charlie", True), ("Delta", False)]
    ih = item_size + 12
    box = item_size
    weight = "bold" if item_bold else "normal"
    for label, checked in items:
        if y + ih > height - 6:
            break
        parts.append(f'<rect x="{pad}" y="{y:.1f}" width="{width - pad * 2}" height="{ih}" fill="{item_bg}"/>')
        # checkbox
        parts.append(f'<rect x="{pad + 4}" y="{y + (ih - box) / 2:.1f}" width="{box}" height="{box}" fill="none" stroke="{item_fg}" stroke-width="1"/>')
        if checked:
            parts.append(f'<rect x="{pad + 6}" y="{y + (ih - box) / 2 + 2:.1f}" width="{box - 4}" height="{box - 4}" fill="{select_col}"/>')
        parts.append(
            f'<text x="{pad + box + 12}" y="{y + item_size + 4:.1f}" font-size="{item_size}" fill="{item_fg}" '
            f'font-weight="{weight}">{_esc(label)}</text>'
        )
        y += ih + 2

    parts.append(title_svg)
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
    rh_italic = _flag(formatting, "rowHeaderItalic", False)
    rh_underline = _flag(formatting, "rowHeaderUnderline", False)
    rh_align = _txt(formatting, "rowHeaderAlignment", "Left")
    rh_stepped = _flag(formatting, "rowHeaderStepped", True)

    grid_outline_color = _col(formatting, "gridOutlineColor", "#CCCCCC")
    grid_outline_weight = _num(formatting, "gridOutlineWeight", 1)

    ch_bg = _col(formatting, "columnHeaderBackgroundColor", accent)
    ch_fg = _col(formatting, "columnHeaderTextColor", fg)
    ch_size = int(_num(formatting, "columnHeaderFontSize", 12))
    ch_bold = _flag(formatting, "columnHeaderFontBold", True)
    ch_italic = _flag(formatting, "columnHeaderItalic", False)
    ch_underline = _flag(formatting, "columnHeaderUnderline", False)
    ch_align = _txt(formatting, "columnHeaderAlignment", "Left")

    v_bg = _col(formatting, "valuesBackgroundColor", theme.background)
    v_fg = _col(formatting, "valuesTextColor", fg)
    v_size = int(_num(formatting, "valuesFontSize", 11))
    v_bold = _flag(formatting, "valuesFontBold", False)
    v_italic = _flag(formatting, "valuesItalic", False)
    v_underline = _flag(formatting, "valuesUnderline", False)
    v_align = _txt(formatting, "valuesAlignment", "Left")
    padding = _num(formatting, "cellPadding", 6)
    banded = _flag(formatting, "bandedRows", False)
    alt_bg = _col(formatting, "alternateRowColor", "#F5F5F5")
    db_show = _flag(formatting, "dataBarsShow", False)
    db_pos = _col(formatting, "dataBarsPositiveColor", accent)
    db_hide = _flag(formatting, "dataBarsHideText", False)

    show_totals = _flag(formatting, "showTotals", True)
    tot_bg = _col(formatting, "totalsBackgroundColor", "#E8E8E8")
    tot_fg = _col(formatting, "totalsTextColor", "#000000")
    tot_size = int(_num(formatting, "totalsFontSize", 12))
    tot_bold = _flag(formatting, "totalsFontBold", True)
    tot_italic = _flag(formatting, "totalsItalic", False)
    tot_underline = _flag(formatting, "totalsUnderline", False)

    show_sub = _flag(formatting, "showSubtotals", True)
    sub_bg = _col(formatting, "subtotalsBackgroundColor", "#F0F0F0")
    sub_fg = _col(formatting, "subtotalsTextColor", fg)
    sub_size = int(_num(formatting, "subtotalsFontSize", 11))
    sub_bold = _flag(formatting, "subtotalsFontBold", True)
    sub_italic = _flag(formatting, "subtotalsItalic", False)
    sub_underline = _flag(formatting, "subtotalsUnderline", False)

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

    db_max = max((float(r[1]) for r in body + data2), default=1.0) or 1.0

    col_w = width / len(cols)
    row_h = max(16, v_size + padding * 2 + row_spacing)
    header_h = max(18, ch_size + padding * 2)
    y = top

    def draw_row(vals, bg, text_color, size, bold, align, is_header=False, indent=0,
                 italic=False, underline=False, bars=False):
        nonlocal y
        h = header_h if is_header else row_h
        parts.append(f'<rect x="0" y="{y:.1f}" width="{width}" height="{h:.1f}" fill="{bg}" opacity="0.55"/>')
        weight = "bold" if bold else "normal"
        style = ' font-style="italic"' if italic else ""
        deco = ' text-decoration="underline"' if underline else ""
        for ci, cell in enumerate(vals):
            if cell == "":
                continue
            # Data bars: a proportional bar in the numeric (2nd) column.
            if bars and ci == 1 and not is_header:
                try:
                    val = float(cell)
                except ValueError:
                    val = None
                if val is not None:
                    frac = max(0.05, min(1.0, val / db_max))
                    parts.append(
                        f'<rect x="{col_w * ci + 4:.1f}" y="{y + h * 0.25:.1f}" '
                        f'width="{(col_w - 8) * frac:.1f}" height="{h * 0.5:.1f}" rx="1" '
                        f'fill="{db_pos}" opacity="0.55"/>'
                    )
                if db_hide:
                    continue  # bars only -- suppress the value text
            # First column follows row-header styling for body rows.
            if ci == 0 and not is_header:
                anc, fx = anchor(rh_align)
                tx = col_w * ci + col_w * fx + (indent if anc == "start" else 0)
                rh_style = ' font-style="italic"' if rh_italic else ""
                rh_deco = ' text-decoration="underline"' if rh_underline else ""
                parts.append(
                    f'<text x="{tx:.1f}" y="{y + h * 0.66:.1f}" font-size="{rh_size}" '
                    f'fill="{rh_fg}" font-weight="{"bold" if rh_bold else "normal"}"{rh_style}{rh_deco} '
                    f'text-anchor="{anc}">{_esc(cell)}</text>'
                )
                continue
            anc, fx = anchor(align)
            tx = col_w * ci + col_w * fx
            parts.append(
                f'<text x="{tx:.1f}" y="{y + h * 0.66:.1f}" font-size="{size}" fill="{text_color}" '
                f'font-weight="{weight}"{style}{deco} text-anchor="{anc}">{_esc(cell)}</text>'
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
    draw_row(cols, ch_bg, ch_fg, ch_size, ch_bold, ch_align, is_header=True, italic=ch_italic, underline=ch_underline)

    data_row = 0

    def value_bg() -> str:
        nonlocal data_row
        # Banded rows alternate the background of every second value row.
        bg = alt_bg if (banded and data_row % 2 == 1) else v_bg
        data_row += 1
        return bg

    # A stepped layout indents child rows beneath their subtotal.
    step = 10 if rh_stepped else 0
    for row in body:
        draw_row(row, value_bg(), v_fg, v_size, v_bold, v_align, indent=step, italic=v_italic, underline=v_underline, bars=db_show)
    if show_sub:
        draw_row(sub_row, sub_bg, sub_fg, sub_size, sub_bold, v_align, italic=sub_italic, underline=sub_underline)
    for row in data2:
        draw_row(row, value_bg(), v_fg, v_size, v_bold, v_align, indent=step, italic=v_italic, underline=v_underline, bars=db_show)
    if show_totals:
        draw_row(tot_row, tot_bg, tot_fg, tot_size, tot_bold, v_align, italic=tot_italic, underline=tot_underline)

    # Outer grid outline.
    if grid_outline_weight > 0:
        parts.append(
            f'<rect x="{grid_outline_weight / 2:.1f}" y="{top:.1f}" '
            f'width="{width - grid_outline_weight:.1f}" height="{y - top:.1f}" '
            f'fill="none" stroke="{grid_outline_color}" stroke-width="{grid_outline_weight}"/>'
        )

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
# Bespoke placeholders for visuals without per-visual formatting
# --------------------------------------------------------------------------- #
def generate_button_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Action button: a pill button with a label."""
    formatting, generic = formatting or {}, generic or {}
    fill = _col(formatting, "buttonFillColor", theme.table_accent)
    text_color = _col(formatting, "buttonTextColor", "#FFFFFF")
    outline = _col(formatting, "buttonOutlineColor", fill)
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Action Button", theme.foreground, generic)
    bw, bh = width * 0.5, 40
    x, y = (width - bw) / 2, top + (height - top - bh) / 2
    parts.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{bh}" rx="7" fill="{fill}" stroke="{outline}" stroke-width="2"/>')
    parts.append(
        f'<text x="{width / 2:.0f}" y="{y + bh / 2 + 5:.0f}" font-size="15" fill="{text_color}" '
        f'text-anchor="middle" font-weight="bold">Submit  &#8594;</text>'
    )
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_shape_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Basic shape: primitive shapes honoring a fill + outline colour."""
    formatting, generic = formatting or {}, generic or {}
    fill = _col(formatting, "shapeFillColor", theme.table_accent)
    outline = _col(formatting, "shapeOutlineColor", "#000000")
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Basic Shape", theme.foreground, generic)
    cy = top + (height - top) / 2
    stroke = f' stroke="{outline}" stroke-width="2"'
    parts.append(f'<rect x="{width * 0.12:.0f}" y="{cy - 26:.0f}" width="52" height="52" rx="8" fill="{fill}"{stroke}/>')
    parts.append(f'<circle cx="{width * 0.5:.0f}" cy="{cy:.0f}" r="28" fill="{fill}"{stroke}/>')
    tx = width * 0.82
    parts.append(f'<polygon points="{tx:.0f},{cy - 28:.0f} {tx - 28:.0f},{cy + 24:.0f} {tx + 28:.0f},{cy + 24:.0f}" fill="{fill}"{stroke}/>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def _pin(cx: float, cy: float, color: str) -> str:
    """A map marker whose point sits at (cx, cy)."""
    return (
        f'<path d="M{cx:.0f},{cy:.0f} C{cx - 9:.0f},{cy - 14:.0f} {cx - 9:.0f},{cy - 24:.0f} {cx:.0f},{cy - 24:.0f} '
        f'C{cx + 9:.0f},{cy - 24:.0f} {cx + 9:.0f},{cy - 14:.0f} {cx:.0f},{cy:.0f} Z" fill="{color}"/>'
        f'<circle cx="{cx:.0f}" cy="{cy - 16:.0f}" r="3.5" fill="#FFFFFF"/>'
    )


def _map_regions(pl, pt, pr, pb):
    w, h = pr - pl, pb - pt
    return [
        f"{pl + w * 0.05:.0f},{pt + h * 0.2:.0f} {pl + w * 0.45:.0f},{pt + h * 0.1:.0f} {pl + w * 0.5:.0f},{pt + h * 0.5:.0f} {pl + w * 0.15:.0f},{pt + h * 0.6:.0f}",
        f"{pl + w * 0.5:.0f},{pt + h * 0.12:.0f} {pl + w * 0.95:.0f},{pt + h * 0.25:.0f} {pl + w * 0.8:.0f},{pt + h * 0.55:.0f} {pl + w * 0.52:.0f},{pt + h * 0.5:.0f}",
        f"{pl + w * 0.15:.0f},{pt + h * 0.62:.0f} {pl + w * 0.52:.0f},{pt + h * 0.55:.0f} {pl + w * 0.6:.0f},{pt + h * 0.92:.0f} {pl + w * 0.2:.0f},{pt + h * 0.95:.0f}",
        f"{pl + w * 0.6:.0f},{pt + h * 0.55:.0f} {pl + w * 0.82:.0f},{pt + h * 0.57:.0f} {pl + w * 0.88:.0f},{pt + h * 0.9:.0f} {pl + w * 0.62:.0f},{pt + h * 0.92:.0f}",
    ]


def generate_map_svg(theme, formatting=None, generic=None, width=300, height=200,
                     style="pins", label="Map"):
    """Map placeholder -- pins, filled regions (choropleth) or outlined shapes."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 4)
    # A single data-point / region / shape colour override.
    data_col = _col(formatting, "mapDataColor", "") or _col(formatting, "shapeMapColor", "")
    border_col = _col(formatting, "shapeMapBorderColor", "#FFFFFF")
    stroke_col = _col(formatting, "mapStrokeColor", "#FFFFFF")
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, label, theme.foreground, generic)
    pl, pt, pr, pb = 10, top + 4, width - 10, height - 10

    if style == "azure":  # faint tile grid behind the land
        for gx in range(int(pl), int(pr), 28):
            parts.append(f'<line x1="{gx}" y1="{pt:.0f}" x2="{gx}" y2="{pb:.0f}" stroke="#DDE6EF" stroke-width="1"/>')
        for gy in range(int(pt), int(pb), 28):
            parts.append(f'<line x1="{pl}" y1="{gy}" x2="{pr}" y2="{gy}" stroke="#DDE6EF" stroke-width="1"/>')

    regions = _map_regions(pl, pt, pr, pb)
    for i, pts in enumerate(regions):
        if style == "filled":
            parts.append(f'<polygon points="{pts}" fill="{data_col or colors[i % len(colors)]}" opacity="0.85" stroke="{stroke_col}" stroke-width="1.5"/>')
        elif style == "outline":
            parts.append(f'<polygon points="{pts}" fill="{data_col or "none"}" stroke="{border_col if data_col else theme.foreground}" stroke-width="1.5" opacity="0.8"/>')
        else:  # land under pins
            parts.append(f'<polygon points="{pts}" fill="#C7D9C7" stroke="#FFFFFF" stroke-width="1"/>')

    if style in ("pins", "azure"):
        pin_cols = [data_col, data_col, data_col] if data_col else [theme.bad, theme.table_accent, theme.good]
        for (fx, fy), col in zip([(0.3, 0.45), (0.62, 0.4), (0.5, 0.78)], pin_cols):
            parts.append(_pin(pl + (pr - pl) * fx, pt + (pb - pt) * fy, col))

    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_decomp_tree_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Decomposition tree: a root node branching to children."""
    formatting, generic = formatting or {}, generic or {}
    node_fill = _col(formatting, "levelHeaderBg", theme.table_accent)
    node_text = _col(formatting, "levelTitleColor", "#FFFFFF")
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Decomposition Tree", theme.foreground, generic)
    nw, nh = 58, 26
    col_x = [12, (width - nw) / 2, width - nw - 12]
    mid = top + (height - top) / 2

    def node(x, y, text, fill):
        parts.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{nw}" height="{nh}" rx="4" fill="{fill}"/>')
        parts.append(f'<text x="{x + nw / 2:.0f}" y="{y + nh / 2 + 4:.0f}" font-size="10" fill="{node_text}" text-anchor="middle">{_esc(text)}</text>')

    child_ys = [top + (height - top) * 0.25, top + (height - top) * 0.7]
    gy = [top + (height - top) * 0.14, top + (height - top) * 0.38, top + (height - top) * 0.62, top + (height - top) * 0.86]
    # connectors
    for cyv in child_ys:
        parts.append(f'<line x1="{col_x[0] + nw:.0f}" y1="{mid + nh / 2:.0f}" x2="{col_x[1]:.0f}" y2="{cyv + nh / 2:.0f}" stroke="#B3B0AD" stroke-width="1.5"/>')
    for i, gyv in enumerate(gy):
        src = child_ys[0] if i < 2 else child_ys[1]
        parts.append(f'<line x1="{col_x[1] + nw:.0f}" y1="{src + nh / 2:.0f}" x2="{col_x[2]:.0f}" y2="{gyv + nh / 2:.0f}" stroke="#B3B0AD" stroke-width="1"/>')
    node(col_x[0], mid, "Total", node_fill)
    node(col_x[1], child_ys[0], "North", node_fill)
    node(col_x[1], child_ys[1], "South", node_fill)
    labels = ["A", "B", "C", "D"]
    cols = _series_colors(theme, 4)
    for i, gyv in enumerate(gy):
        node(col_x[2], gyv, labels[i], cols[i])
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_image_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Image placeholder: a classic picture icon."""
    generic = generic or {}
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Image", theme.foreground, generic)
    x, y = width * 0.2, top + 8
    w, h = width * 0.6, height - top - 22
    parts.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="4" fill="#EDEBE9" stroke="#B3B0AD" stroke-width="1.5"/>')
    parts.append(f'<circle cx="{x + w * 0.28:.0f}" cy="{y + h * 0.3:.0f}" r="{h * 0.09:.0f}" fill="#F2C811"/>')
    base = y + h - 6
    parts.append(f'<polygon points="{x + 6:.0f},{base:.0f} {x + w * 0.4:.0f},{y + h * 0.45:.0f} {x + w * 0.62:.0f},{base:.0f}" fill="#8A8886"/>')
    parts.append(f'<polygon points="{x + w * 0.45:.0f},{base:.0f} {x + w * 0.72:.0f},{y + h * 0.55:.0f} {x + w - 6:.0f},{base:.0f}" fill="#605E5C"/>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_key_influencers_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Key influencers/drivers: an influencer bubble beside contributing bars."""
    generic = generic or {}
    colors = _series_colors(theme, 3)
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Key Drivers", theme.foreground, generic)
    cx, cy = width * 0.26, top + (height - top) / 2
    parts.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{min(38, (height - top) * 0.28):.0f}" fill="{colors[0]}" opacity="0.9"/>')
    parts.append(f'<text x="{cx:.0f}" y="{cy - 2:.0f}" font-size="18" fill="#FFFFFF" text-anchor="middle" font-weight="bold">2.6x</text>')
    parts.append(f'<text x="{cx:.0f}" y="{cy + 16:.0f}" font-size="9" fill="#FFFFFF" text-anchor="middle">likely</text>')
    bx = width * 0.5
    bw = width * 0.42
    for i, frac in enumerate((1.0, 0.72, 0.48)):
        by = top + 14 + i * ((height - top - 20) / 3)
        parts.append(f'<rect x="{bx:.0f}" y="{by:.0f}" width="{bw * frac:.0f}" height="16" rx="3" fill="{colors[i % 3]}" opacity="0.85"/>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_script_visual_svg(theme, formatting=None, generic=None, width=300, height=200,
                               lang="PY", label="Script Visual"):
    """Python/R visual: a small chart with a language badge."""
    generic = generic or {}
    colors = _series_colors(theme, 2)
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, label, theme.foreground, generic)
    pl, pt, pr, pb = 24, top + 8, width - 14, height - 24
    parts.append(f'<line x1="{pl}" y1="{pb}" x2="{pr}" y2="{pb}" stroke="{theme.foreground}" stroke-width="1"/>')
    parts.append(f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{pb}" stroke="{theme.foreground}" stroke-width="1"/>')
    rng = random.Random(hash(lang) & 0xFFFF)
    for i in range(22):
        px = pl + (pr - pl) * rng.random()
        py = pt + (pb - pt) * rng.random()
        parts.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="3.5" fill="{colors[i % 2]}" opacity="0.8"/>')
    parts.append(f'<rect x="{pr - 30:.0f}" y="{pt:.0f}" width="28" height="18" rx="4" fill="{theme.table_accent}"/>')
    parts.append(f'<text x="{pr - 16:.0f}" y="{pt + 13:.0f}" font-size="11" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{_esc(lang)}</text>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_qna_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Q&A: a question input box with a suggestion chip."""
    generic = generic or {}
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Q&A", theme.foreground, generic)
    bx, bw = width * 0.1, width * 0.8
    by = top + (height - top) * 0.34
    parts.append(f'<rect x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" height="34" rx="17" fill="#FFFFFF" stroke="{theme.table_accent}" stroke-width="1.5"/>')
    mx, my = bx + 22, by + 17
    parts.append(f'<circle cx="{mx:.0f}" cy="{my - 1:.0f}" r="6" fill="none" stroke="{theme.foreground}" stroke-width="2"/>')
    parts.append(f'<line x1="{mx + 4:.0f}" y1="{my + 3:.0f}" x2="{mx + 9:.0f}" y2="{my + 8:.0f}" stroke="{theme.foreground}" stroke-width="2"/>')
    parts.append(f'<text x="{bx + 40:.0f}" y="{by + 22:.0f}" font-size="12" fill="#8A8886">Ask a question about your data</text>')
    parts.append(f'<rect x="{bx:.0f}" y="{by + 46:.0f}" width="{bw * 0.5:.0f}" height="22" rx="11" fill="{theme.table_accent}" opacity="0.15"/>')
    parts.append(f'<text x="{bx + 14:.0f}" y="{by + 61:.0f}" font-size="10" fill="{theme.table_accent}">total sales by region</text>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_text_svg(theme, formatting=None, generic=None, width=300, height=200,
                      kind="text", label="Text Box"):
    """Text box / smart narrative: rendered sample text honoring colour & size."""
    formatting, generic = formatting or {}, generic or {}
    fg = theme.foreground
    if kind == "narrative":
        text_col = _col(formatting, "narrativeTextColor", fg)
        size = int(_num(formatting, "narrativeFontSize", 12))
        align = _txt(formatting, "narrativeAlignment", "Left")
        lines = ["Sales grew 12% this quarter,",
                 "led by the North region with",
                 "double-digit gains across Q4."]
    else:
        text_col = _col(formatting, "textColor", fg)
        size = int(_num(formatting, "textFontSize", 14))
        align = "Left"
        lines = ["Heading text", "Body copy that flows", "across several lines here."]

    anchor, ax = {
        "Center": ("middle", width / 2),
        "Right": ("end", width - 16),
    }.get(align, ("start", 16.0))

    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, label, fg, generic)
    y = top + 10 + size
    if kind == "narrative":  # a summary accent bar
        parts.append(f'<rect x="16" y="{y - size:.0f}" width="{width * 0.5:.0f}" height="{max(6, size - 2)}" rx="3" fill="{theme.table_accent}" opacity="0.85"/>')
        y += size + 10
    for ln in lines:
        if y > height - 6:
            break
        parts.append(
            f'<text x="{ax:.0f}" y="{y:.0f}" font-size="{size}" fill="{text_col}" '
            f'text-anchor="{anchor}">{_esc(ln)}</text>'
        )
        y += size + 8
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_scorecard_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Scorecard (Goals): metric rows with current value, target and a status dot."""
    generic = generic or {}
    fg = theme.foreground
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Scorecard", fg, generic)
    rows = [("Revenue", "$1.2M", "$1.0M", theme.good),
            ("Churn", "6.4%", "5.0%", theme.bad),
            ("NPS", "48", "45", theme.good)]
    y = top + 6
    rh = min(30, (height - top - 10) / len(rows))
    parts.append(f'<text x="12" y="{y + 8:.0f}" font-size="9" fill="#8A8886">Metric</text>')
    parts.append(f'<text x="{width - 90:.0f}" y="{y + 8:.0f}" font-size="9" fill="#8A8886">Value</text>')
    parts.append(f'<text x="{width - 40:.0f}" y="{y + 8:.0f}" font-size="9" fill="#8A8886">Goal</text>')
    y += 14
    for name, val, goal, dot in rows:
        parts.append(f'<circle cx="17" cy="{y + rh / 2:.0f}" r="4" fill="{dot}"/>')
        parts.append(f'<text x="28" y="{y + rh / 2 + 4:.0f}" font-size="11" fill="{fg}">{_esc(name)}</text>')
        parts.append(f'<text x="{width - 90:.0f}" y="{y + rh / 2 + 4:.0f}" font-size="11" fill="{fg}" font-weight="bold">{_esc(val)}</text>')
        parts.append(f'<text x="{width - 40:.0f}" y="{y + rh / 2 + 4:.0f}" font-size="10" fill="#8A8886">{_esc(goal)}</text>')
        parts.append(f'<line x1="10" y1="{y + rh:.0f}" x2="{width - 10}" y2="{y + rh:.0f}" stroke="#EDEBE9" stroke-width="1"/>')
        y += rh
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_filter_pane_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Filter pane: a header plus a couple of filter field cards with checkboxes."""
    generic = generic or {}
    fg = theme.foreground
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Filters", fg, generic)
    y = top + 6
    for field in ("Region", "Category"):
        parts.append(f'<rect x="10" y="{y:.0f}" width="{width - 20}" height="46" rx="3" fill="#FAF9F8" stroke="#EDEBE9" stroke-width="1"/>')
        parts.append(f'<text x="18" y="{y + 15:.0f}" font-size="10" fill="{fg}" font-weight="bold">{field}</text>')
        for i, opt in enumerate(("All", "Selected")):
            oy = y + 24 + i * 0  # single row
            ox = 18 + i * 90
            parts.append(f'<rect x="{ox}" y="{y + 26:.0f}" width="9" height="9" fill="none" stroke="{fg}" stroke-width="1"/>')
            if i == 1:
                parts.append(f'<rect x="{ox + 2}" y="{y + 28:.0f}" width="5" height="5" fill="{theme.table_accent}"/>')
            parts.append(f'<text x="{ox + 14}" y="{y + 34:.0f}" font-size="9" fill="{fg}">{opt}</text>')
        y += 54
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_group_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Group container: a dashed frame holding a couple of child shapes."""
    generic = generic or {}
    colors = _series_colors(theme, 2)
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Group", theme.foreground, generic)
    gx, gy = 16, top + 8
    gw, gh = width - 32, height - top - 20
    parts.append(f'<rect x="{gx}" y="{gy:.0f}" width="{gw}" height="{gh:.0f}" rx="4" fill="none" stroke="#B3B0AD" stroke-width="1.5" stroke-dasharray="5,3"/>')
    parts.append(f'<rect x="{gx + 14}" y="{gy + gh * 0.28:.0f}" width="{gw * 0.32:.0f}" height="{gh * 0.45:.0f}" rx="3" fill="{colors[0]}" opacity="0.85"/>')
    parts.append(f'<circle cx="{gx + gw * 0.72:.0f}" cy="{gy + gh * 0.5:.0f}" r="{gh * 0.24:.0f}" fill="{colors[1]}" opacity="0.85"/>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_navigator_svg(theme, formatting=None, generic=None, width=300, height=200,
                           kind="page", label="Navigator"):
    """Page / bookmark navigator: a row of pill buttons, one selected."""
    generic = generic or {}
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, label, theme.foreground, generic)
    items = ["Overview", "Detail", "Trends"] if kind == "page" else ["View A", "View B", "View C"]
    accent = theme.table_accent
    y = top + (height - top) / 2 - 14
    bw = (width - 20 - (len(items) - 1) * 8) / len(items)
    for i, it in enumerate(items):
        x = 10 + i * (bw + 8)
        sel = (i == 0)
        fill = accent if sel else "#FFFFFF"
        stroke = accent
        tcol = "#FFFFFF" if sel else accent
        parts.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="28" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + bw / 2:.0f}" y="{y + 18:.0f}" font-size="10" fill="{tcol}" text-anchor="middle">{_esc(it)}</text>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_page_svg(theme, formatting=None, generic=None, width=300, height=200,
                      kind="page", label="Page"):
    """Page / report canvas: a wallpaper with visual tiles (+ a filter pane strip)."""
    generic = generic or {}
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, label, theme.foreground, generic)
    accent = theme.table_accent
    cl, ct = 12, top + 8
    cr, cb = width - 12, height - 12
    fp = 46 if kind == "report" else 0  # report reserves a filter-pane strip on the right
    # canvas / wallpaper
    parts.append(f'<rect x="{cl}" y="{ct:.0f}" width="{cr - cl}" height="{cb - ct:.0f}" rx="3" fill="#F3F2F1" stroke="#E1DFDD" stroke-width="1"/>')
    tiles_r = cr - fp - 6
    tw = (tiles_r - cl - 18) / 2
    th = (cb - ct - 18) / 2
    for r in range(2):
        for c in range(2):
            tx = cl + 6 + c * (tw + 6)
            ty = ct + 6 + r * (th + 6)
            parts.append(f'<rect x="{tx:.0f}" y="{ty:.0f}" width="{tw:.0f}" height="{th:.0f}" rx="2" fill="#FFFFFF" stroke="#E1DFDD" stroke-width="1"/>')
            parts.append(f'<rect x="{tx + 4:.0f}" y="{ty + 4:.0f}" width="{tw - 8:.0f}" height="4" rx="2" fill="{accent}" opacity="0.7"/>')
    if fp:
        parts.append(f'<rect x="{cr - fp:.0f}" y="{ct:.0f}" width="{fp}" height="{cb - ct:.0f}" fill="#FAF9F8" stroke="#E1DFDD" stroke-width="1"/>')
        parts.append(f'<text x="{cr - fp + 6:.0f}" y="{ct + 14:.0f}" font-size="8" fill="#8A8886">Filters</text>')
        for i in range(3):
            parts.append(f'<rect x="{cr - fp + 6:.0f}" y="{ct + 20 + i * 14:.0f}" width="{fp - 12}" height="9" rx="2" fill="#EDEBE9"/>')
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_paginated_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Paginated (RDL) report: a document page with a header band and table rows."""
    generic = generic or {}
    fg = theme.foreground
    parts = _frame(width, height, generic, theme.background)
    title_svg, top = _title(width, "Paginated Report", fg, generic)
    dx, dy = width * 0.16, top + 8
    dw, dh = width * 0.68, height - top - 20
    parts.append(f'<rect x="{dx:.0f}" y="{dy:.0f}" width="{dw:.0f}" height="{dh:.0f}" fill="#FFFFFF" stroke="#B3B0AD" stroke-width="1.5"/>')
    parts.append(f'<rect x="{dx:.0f}" y="{dy:.0f}" width="{dw:.0f}" height="16" fill="{theme.table_accent}" opacity="0.85"/>')
    ry = dy + 24
    while ry < dy + dh - 6:
        parts.append(f'<line x1="{dx + 8:.0f}" y1="{ry:.0f}" x2="{dx + dw - 8:.0f}" y2="{ry:.0f}" stroke="#E1DFDD" stroke-width="1"/>')
        parts.append(f'<rect x="{dx + 8:.0f}" y="{ry - 6:.0f}" width="{dw * 0.4:.0f}" height="4" rx="1" fill="#C8C6C4"/>')
        ry += 14
    parts.append(title_svg)
    parts.append("</svg>")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
_TABLE_KEYS = {"matrix", "table", "tableEx", "pivotTable"}
_CARD_KEYS = {"card"}
_BAR_KEYS = {"barChart", "columnChart", "clusteredBarChart", "clusteredColumnChart"}


def render_visual_preview(
    theme: PowerBITheme,
    visual_key: str,
    style_obj: Dict[str, Any] | None = None,
    width: int = 250,
    height: int = 200,
) -> str:
    """Render the mockup that matches *visual_key* from a stored ``"*"`` style object."""
    style_obj = style_obj or {}
    formatting = style_obj.get("formatting", {}) if isinstance(style_obj, dict) else {}
    generic = extract_generic(style_obj)
    args = (theme, formatting, generic, width, height)

    # Tables & cards
    if visual_key in _TABLE_KEYS:
        return generate_table_svg(*args)
    if visual_key in _CARD_KEYS:
        return generate_card_kpi_svg(*args)
    if visual_key == "multiRowCard":
        return generate_multirow_card_svg(*args)
    if visual_key == "kpi":
        return generate_kpi_svg(*args)

    # Non-cartesian charts (own settings sets)
    if visual_key == "pieChart":
        return generate_pie_chart_svg(*args)
    if visual_key == "donutChart":
        return generate_pie_chart_svg(*args, donut=True)
    if visual_key == "gauge":
        return generate_gauge_svg(*args)
    if visual_key == "treemap":
        return generate_treemap_svg(*args)
    if visual_key == "funnel":
        return generate_funnel_svg(*args)
    if visual_key == "slicer":
        return generate_slicer_svg(*args)

    # Cartesian charts (share CHART_SECTIONS)
    if visual_key == "lineChart":
        return generate_line_chart_svg(*args)
    if visual_key == "areaChart":
        return generate_area_chart_svg(*args)
    if visual_key == "stackedAreaChart":
        return generate_area_chart_svg(*args, label="Stacked Area", stacked=True)
    if visual_key == "hundredPercentStackedAreaChart":
        return generate_area_chart_svg(*args, label="100% Stacked Area", stacked=True, percent=True)
    if visual_key in ("lineClusteredColumnComboChart", "lineStackedColumnComboChart"):
        return generate_combo_chart_svg(*args, stacked=visual_key.startswith("lineStacked"))
    if visual_key in ("hundredPercentStackedBarChart", "hundredPercentStackedColumnChart"):
        return generate_stacked_chart_svg(*args, percent=True)
    if visual_key == "scatterChart":
        return generate_scatter_chart_svg(*args)
    if visual_key == "waterfallChart":
        return generate_waterfall_chart_svg(*args)
    if visual_key == "ribbonChart":
        return generate_ribbon_chart_svg(*args)

    # Non-customizable visuals: bespoke placeholders
    if visual_key == "actionButton":
        return generate_button_svg(*args)
    if visual_key == "basicShape":
        return generate_shape_svg(*args)
    if visual_key == "map":
        return generate_map_svg(*args, style="pins", label="Map")
    if visual_key == "azureMapVisual":
        return generate_map_svg(*args, style="azure", label="Azure Maps")
    if visual_key == "filledMap":
        return generate_map_svg(*args, style="filled", label="Filled Map")
    if visual_key == "shapeMap":
        return generate_map_svg(*args, style="outline", label="Shape Map")
    if visual_key == "decompositionTreeVisual":
        return generate_decomp_tree_svg(*args)
    if visual_key == "image":
        return generate_image_svg(*args)
    if visual_key == "keyDriversVisual":
        return generate_key_influencers_svg(*args)
    if visual_key == "pythonVisual":
        return generate_script_visual_svg(*args, lang="PY", label="Python Visual")
    if visual_key == "rVisual":
        return generate_script_visual_svg(*args, lang="R", label="R Visual")
    if visual_key == "qnaVisual":
        return generate_qna_svg(*args)
    if visual_key == "smartNarrative":
        return generate_text_svg(*args, kind="narrative", label="Smart Narrative")
    if visual_key == "textbox":
        return generate_text_svg(*args, kind="text", label="Text Box")

    # Newer container / slicer / navigator / goal visuals -- bespoke placeholders.
    if visual_key == "cardVisual":
        return generate_card_kpi_svg(*args)
    if visual_key in ("advancedSlicerVisual", "listSlicer", "textSlicer"):
        return generate_slicer_svg(*args)
    if visual_key == "pageNavigator":
        return generate_navigator_svg(*args, kind="page", label="Page Navigator")
    if visual_key == "bookmarkNavigator":
        return generate_navigator_svg(*args, kind="bookmark", label="Bookmark Navigator")
    if visual_key == "scorecard":
        return generate_scorecard_svg(*args)
    if visual_key == "filter":
        return generate_filter_pane_svg(*args)
    if visual_key == "group":
        return generate_group_svg(*args)
    if visual_key == "page":
        return generate_page_svg(*args, kind="page", label="Page")
    if visual_key == "report":
        return generate_page_svg(*args, kind="report", label="Report")
    if visual_key == "rdlVisual":
        return generate_paginated_svg(*args)

    # Default: grouped bar/column chart (bar / column / clustered family)
    return generate_bar_chart_svg(*args)


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
