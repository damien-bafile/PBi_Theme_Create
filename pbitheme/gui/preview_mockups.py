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
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape

from ..model import (
    PowerBITheme,
    unpack_background_object,
    unpack_border_object,
    unpack_drop_shadow_object,
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


def _series_colors(theme: PowerBITheme, n: int = 3) -> List[str]:
    colors = list(theme.data_colors[:n]) if theme.data_colors else []
    if not colors:
        colors = [theme.table_accent]
    while len(colors) < n:
        colors.append(colors[-1])
    return colors


def _data_label(x: float, y: float, text: Any, formatting: Dict[str, Any],
                generic: Dict[str, Any], with_bg: bool = False) -> List[str]:
    """A single chart data label honoring generic labels or the chart dataLabel fields."""
    color = generic["labels"]["color"] if (generic or {}).get("labels") else _col(formatting, "dataLabelColor", "#252423")
    size = int(generic["labels"]["size"]) if (generic or {}).get("labels") else int(_num(formatting, "dataLabelFontSize", 8))
    with_bg = with_bg or _flag(formatting, "dataLabelBackground", False)
    parts: List[str] = []
    if with_bg:
        parts.append(
            f'<rect x="{x - 9:.1f}" y="{y - size:.1f}" width="18" height="{size + 3}" fill="#FFFFFF" opacity="0.7"/>'
        )
    parts.append(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="middle">{_esc(text)}</text>'
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


def generate_area_chart_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Line chart with the area under each series filled."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 3)
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Area Chart")
    series = [[40, 55, 50, 70, 65, 80], [30, 40, 45, 55, 60, 68], [20, 28, 35, 42, 48, 58]]
    scale = (pb - pt) / 100.0
    n = len(series[0])
    step = (pr - pl) / (n - 1)
    for si in reversed(range(len(series))):  # back-to-front so fills overlap nicely
        line = series[si]
        pts = [(pl + i * step, pb - v * scale) for i, v in enumerate(line)]
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
    colors = _series_colors(theme, 3)
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
    colors = _series_colors(theme, 3)
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
                parts += _data_label(x + bw / 2, y0 - h / 2 + 3, f"{round(100 * v / total)}%", formatting, generic)
            y0 -= h
    parts.append("</svg>")
    return "\n".join(parts)


def generate_scatter_chart_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Scatter plot: points across the X/Y plane, coloured by series."""
    formatting, generic = formatting or {}, generic or {}
    colors = _series_colors(theme, 3)
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Scatter Chart")
    pts_by_series = [
        [(0.15, 0.30), (0.30, 0.55), (0.45, 0.40), (0.60, 0.70), (0.80, 0.62)],
        [(0.20, 0.65), (0.38, 0.35), (0.55, 0.52), (0.70, 0.30), (0.88, 0.45)],
        [(0.25, 0.20), (0.50, 0.80), (0.65, 0.60), (0.82, 0.78), (0.35, 0.72)],
    ]
    labels_on = _labels_on(formatting, generic)
    for si, pts in enumerate(pts_by_series):
        for fx, fy in pts:
            cx = pl + fx * (pr - pl)
            cy = pb - fy * (pb - pt)
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{colors[si]}" opacity="0.85"/>')
            if labels_on and si == 0:
                parts += _data_label(cx, cy - 6, round(fy * 100), formatting, generic)
    parts.append("</svg>")
    return "\n".join(parts)


def generate_waterfall_chart_svg(theme, formatting=None, generic=None, width=300, height=200):
    """Waterfall: floating step bars (increase / decrease / total) with connectors."""
    formatting, generic = formatting or {}, generic or {}
    parts, pl, pt, pr, pb = _chart_base(theme, formatting, generic, width, height, "Waterfall")
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
            color = theme.table_accent
        else:
            start = running
            running += delta
            lo, hi = min(start, running), max(start, running)
            bottom, top = pb - lo * scale, pb - hi * scale
            color = theme.good if (kind == "inc" or kind == "start") else theme.bad
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
    colors = _series_colors(theme, 3)
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
    inner = r * 0.55 if donut else 0.0

    total = sum(vals)
    show_labels = _flag(formatting, "showDataLabels", True)
    dl_color = _col(formatting, "dataLabelColor", "#FFFFFF")
    dl_size = int(_num(formatting, "dataLabelFontSize", 9))
    angle = 90.0  # start at top
    for i, v in enumerate(vals):
        sweep = 360.0 * v / total
        parts.append(_wedge(cx, cy, r, angle, angle + sweep, colors[i], inner))
        if show_labels:
            mid = angle + sweep / 2
            lx, ly = _pt(cx, cy, (r + inner) / 2 if donut else r * 0.62, mid)
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + dl_size / 3:.1f}" font-size="{dl_size}" fill="{dl_color}" '
                f'text-anchor="middle">{round(100 * v / total)}%</text>'
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
    target = vmin + (vmax - vmin) * 0.85
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
                f'<text x="{bx + 5:.1f}" y="{by + dl_size + 3:.1f}" font-size="{dl_size}" fill="{dl_color}">{_esc(lab)}</text>'
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
                f'text-anchor="middle">{_esc(label)}: {v}</text>'
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
            parts.append(f'<rect x="{pad + 6}" y="{y + (ih - box) / 2 + 2:.1f}" width="{box - 4}" height="{box - 4}" fill="{accent}"/>')
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

    # Default: grouped bar/column chart
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
