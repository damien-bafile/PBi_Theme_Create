"""Translate the app's internal visual styles into valid Power BI theme cards.

The editor keeps per-visual settings in a convenience ``formatting`` block with
flat keys (``xAxisLabelColor``, ``gridlineStyle``, ``rowHeaderTextColor`` ...).
Power BI's theme schema does **not** have a ``formatting`` card -- it expects
named cards (``categoryAxis``, ``valueAxis``, ``legend``, ``labels``, ``grid``,
``columnHeaders``, ``values``, ``total`` ...), each an array of property objects,
with colours written as ``{"solid": {"color": "#RRGGBB"}}``.

This module maps the flat keys onto the real cards (names and value types verified
against microsoft/powerbi-desktop-samples reportThemeSchema) so exported themes
import cleanly. Card names the app already emits correctly (``title``, ``legend``,
``background``, ``border``, ``labels`` from the generic-override section) pass
through and are merged property-wise, with the explicit generic values winning.

It also maps the app's visual keys to Power BI's real visual names where they
differ: Matrix -> ``pivotTable`` and Table -> ``tableEx``.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .model import _solid_color, _first, _extract_solid_color, is_valid_hex

# App visual key -> Power BI visualStyles visual name (only where they differ).
VISUAL_NAME_MAP = {
    "matrix": "pivotTable",
    "table": "tableEx",
}

# Families (by app key) that share a translation.
_CARTESIAN = {
    "barChart", "columnChart", "clusteredBarChart", "clusteredColumnChart",
    "hundredPercentStackedBarChart", "hundredPercentStackedColumnChart",
    "lineChart", "areaChart", "lineClusteredColumnComboChart",
    "lineStackedColumnComboChart", "ribbonChart", "waterfallChart",
}
_SCATTER = {"scatterChart"}
_PIE = {"pieChart", "donutChart"}
_TREEMAP = {"treemap"}
_FUNNEL = {"funnel"}
_GAUGE = {"gauge"}
_TABLE_PLAIN = {"table", "tableEx"}
_MATRIX = {"matrix", "pivotTable"}
_CARD = {"card"}
_MULTIROW = {"multiRowCard"}
_SLICER = {"slicer"}
_KPI = {"kpi"}

_GRIDLINE_STYLE = {"Solid": "solid", "Dashed": "dashed", "Dotted": "dotted"}


def _fill(hex_color: str) -> Dict[str, Any] | None:
    return _solid_color(hex_color) if is_valid_hex(hex_color) else None


def _set(card: Dict[str, Any], key: str, value: Any) -> None:
    """Set a card property, skipping None (e.g. an invalid colour)."""
    if value is not None:
        card[key] = value


def _axis_gridlines(card: Dict[str, Any], fmt: Dict[str, Any]) -> None:
    style = fmt.get("gridlineStyle")
    if style is not None:
        if style == "None":
            card["gridlineShow"] = False
        else:
            card["gridlineShow"] = True
            card["gridlineStyle"] = _GRIDLINE_STYLE.get(style, "solid")
    if "gridlineColor" in fmt:
        _set(card, "gridlineColor", _fill(fmt["gridlineColor"]))
    if "gridlineThickness" in fmt:
        card["gridlineThickness"] = fmt["gridlineThickness"]


def _translate_formatting(app_key: str, fmt: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Map a flat ``formatting`` dict onto real Power BI cards for *app_key*."""
    cards: Dict[str, Dict[str, Any]] = {}
    if not fmt:
        return cards

    def card(name: str) -> Dict[str, Any]:
        return cards.setdefault(name, {})

    # ---- Cartesian charts + scatter share axes / legend ---- #
    if app_key in _CARTESIAN | _SCATTER:
        cat = card("categoryAxis")
        _set(cat, "labelColor", _fill(fmt.get("xAxisLabelColor", "")))
        if "xAxisLabelFontSize" in fmt:
            cat["fontSize"] = fmt["xAxisLabelFontSize"]
        _set(cat, "titleColor", _fill(fmt.get("xAxisTitleColor", "")))
        if "xAxisTitleFontSize" in fmt:
            cat["titleFontSize"] = fmt["xAxisTitleFontSize"]
        if fmt.get("xAxisTitleText"):
            cat["titleText"] = fmt["xAxisTitleText"]
            cat["showAxisTitle"] = True

        val = card("valueAxis")
        _set(val, "labelColor", _fill(fmt.get("yAxisLabelColor", "")))
        if "yAxisLabelFontSize" in fmt:
            val["fontSize"] = fmt["yAxisLabelFontSize"]
        _set(val, "titleColor", _fill(fmt.get("yAxisTitleColor", "")))
        if "yAxisTitleFontSize" in fmt:
            val["titleFontSize"] = fmt["yAxisTitleFontSize"]
        if fmt.get("yAxisTitleText"):
            val["titleText"] = fmt["yAxisTitleText"]
            val["showAxisTitle"] = True
        if "yAxisLogScale" in fmt:
            val["logAxisScale"] = bool(fmt["yAxisLogScale"])
        if fmt.get("yAxisSetRange"):
            if "yAxisStart" in fmt:
                val["start"] = fmt["yAxisStart"]
            if "yAxisEnd" in fmt:
                val["end"] = fmt["yAxisEnd"]
        _axis_gridlines(val, fmt)

        leg = card("legend")
        if "legendPosition" in fmt:
            leg["position"] = fmt["legendPosition"]
        _set(leg, "labelColor", _fill(fmt.get("legendTextColor", "")))
        if "legendFontSize" in fmt:
            leg["fontSize"] = fmt["legendFontSize"]
        if "legendShowTitle" in fmt:
            leg["showTitle"] = bool(fmt["legendShowTitle"])
        if fmt.get("legendTitleText"):
            leg["titleText"] = fmt["legendTitleText"]

        if app_key == "waterfallChart":
            # Waterfall colours the increase / decrease / total bars via sentimentColors.
            sc = card("sentimentColors")
            _set(sc, "increaseFill", _fill(fmt.get("defaultColor", "")))
            _set(sc, "decreaseFill", _fill(fmt.get("decreaseColor", "")))
            _set(sc, "totalFill", _fill(fmt.get("totalColor", "")))
        else:
            _set(card("dataPoint"), "defaultColor", _fill(fmt.get("defaultColor", "")))

        # Scatter has no `labels` card -- data labels live on `categoryLabels`.
        label_card = "categoryLabels" if app_key in _SCATTER else "labels"
        lab = card(label_card)
        _set(lab, "color", _fill(fmt.get("dataLabelColor", "")))
        if "dataLabelFontSize" in fmt:
            lab["fontSize"] = fmt["dataLabelFontSize"]
        if app_key not in _SCATTER and "dataLabelBackground" in fmt:
            lab["enableBackground"] = bool(fmt["dataLabelBackground"])
        if app_key not in _SCATTER:
            if "dataLabelDisplayUnits" in fmt:
                lab["labelDisplayUnits"] = int(fmt["dataLabelDisplayUnits"])
            if "dataLabelPrecision" in fmt:
                lab["labelPrecision"] = int(fmt["dataLabelPrecision"])
            if fmt.get("dataLabelPosition") and fmt["dataLabelPosition"] != "Auto":
                lab["labelPosition"] = fmt["dataLabelPosition"]
        # Drop an empty card so we don't emit `[{}]`.
        if not lab:
            cards.pop(label_card, None)

    # ---- Pie / donut / treemap: legend + slice labels ---- #
    elif app_key in _PIE | _TREEMAP:
        leg = card("legend")
        if "legendPosition" in fmt:
            leg["position"] = fmt["legendPosition"]
        _set(leg, "labelColor", _fill(fmt.get("legendTextColor", "")))
        if "legendFontSize" in fmt:
            leg["fontSize"] = fmt["legendFontSize"]
        lab = card("labels")
        if "showDataLabels" in fmt:
            lab["show"] = bool(fmt["showDataLabels"])
        _set(lab, "color", _fill(fmt.get("dataLabelColor", "")))
        if "dataLabelFontSize" in fmt:
            lab["fontSize"] = fmt["dataLabelFontSize"]

    # ---- Funnel: bar colour + data labels ---- #
    elif app_key in _FUNNEL:
        _set(card("dataPoint"), "defaultColor", _fill(fmt.get("barColor", "")))
        lab = card("labels")
        if "showDataLabels" in fmt:
            lab["show"] = bool(fmt["showDataLabels"])
        _set(lab, "color", _fill(fmt.get("dataLabelColor", "")))
        if "dataLabelFontSize" in fmt:
            lab["fontSize"] = fmt["dataLabelFontSize"]

    # ---- Gauge: axis range, fill, target, callout ---- #
    elif app_key in _GAUGE:
        ax = card("axis")
        if "minValue" in fmt:
            ax["min"] = fmt["minValue"]
        if "maxValue" in fmt:
            ax["max"] = fmt["maxValue"]
        if "targetValue" in fmt:
            ax["target"] = fmt["targetValue"]
        _set(card("dataPoint"), "fill", _fill(fmt.get("fillColor", "")))
        _set(card("target"), "color", _fill(fmt.get("targetColor", "")))
        co = card("calloutValue")
        if "showCallout" in fmt:
            co["show"] = bool(fmt["showCallout"])
        _set(co, "color", _fill(fmt.get("calloutColor", "")))
        # calloutValue has no fontSize property; that size comes from the
        # `callout` text class, so calloutFontSize is intentionally not mapped.

    # ---- Table (tableEx) and Matrix (pivotTable) ---- #
    elif app_key in _TABLE_PLAIN | _MATRIX:
        is_matrix = app_key in _MATRIX
        grid = card("grid")
        style = fmt.get("gridlineStyle")
        if style is not None:
            on = style != "None"
            grid["gridHorizontal"] = on
            grid["gridVertical"] = on
        if "gridlineColor" in fmt:
            gc = _fill(fmt["gridlineColor"])
            _set(grid, "gridHorizontalColor", gc)
            _set(grid, "gridVerticalColor", gc)
        if "gridlineThickness" in fmt:
            grid["gridHorizontalWeight"] = fmt["gridlineThickness"]
            grid["gridVerticalWeight"] = fmt["gridlineThickness"]
        if "rowSpacing" in fmt:
            grid["rowPadding"] = fmt["rowSpacing"]
        _set(grid, "outlineColor", _fill(fmt.get("gridOutlineColor", "")))
        if "gridOutlineWeight" in fmt:
            grid["outlineWeight"] = fmt["gridOutlineWeight"]

        ch = card("columnHeaders")
        _set(ch, "backColor", _fill(fmt.get("columnHeaderBackgroundColor", "")))
        _set(ch, "fontColor", _fill(fmt.get("columnHeaderTextColor", "")))
        if "columnHeaderFontSize" in fmt:
            ch["fontSize"] = fmt["columnHeaderFontSize"]
        if "columnHeaderFontBold" in fmt:
            ch["bold"] = bool(fmt["columnHeaderFontBold"])
        if "columnHeaderItalic" in fmt:
            ch["italic"] = bool(fmt["columnHeaderItalic"])
        if "columnHeaderAlignment" in fmt:
            ch["alignment"] = fmt["columnHeaderAlignment"]
        if fmt.get("columnHeaderFontFamily"):
            ch["fontFamily"] = fmt["columnHeaderFontFamily"]
        if "columnHeaderWordWrap" in fmt:
            ch["wordWrap"] = bool(fmt["columnHeaderWordWrap"])

        vals = card("values")
        _set(vals, "fontColor", _fill(fmt.get("valuesTextColor", "")))
        if "valuesFontSize" in fmt:
            vals["fontSize"] = fmt["valuesFontSize"]
        if "valuesItalic" in fmt:
            vals["italic"] = bool(fmt["valuesItalic"])
        if fmt.get("valuesFontFamily"):
            vals["fontFamily"] = fmt["valuesFontFamily"]
        if "valuesWordWrap" in fmt:
            vals["wordWrap"] = bool(fmt["valuesWordWrap"])
        if fmt.get("bandedRows"):
            # Alternating row colours use the primary/secondary value backgrounds.
            _set(vals, "backColorPrimary", _fill(fmt.get("valuesBackgroundColor", "")))
            _set(vals, "backColorSecondary", _fill(fmt.get("alternateRowColor", "")))
        else:
            _set(vals, "backColor", _fill(fmt.get("valuesBackgroundColor", "")))

        tot = card("total")
        if "showTotals" in fmt:
            tot["totals"] = bool(fmt["showTotals"])
        _set(tot, "backColor", _fill(fmt.get("totalsBackgroundColor", "")))
        _set(tot, "fontColor", _fill(fmt.get("totalsTextColor", "")))
        if "totalsFontBold" in fmt:
            tot["bold"] = bool(fmt["totalsFontBold"])
        if "totalsItalic" in fmt:
            tot["italic"] = bool(fmt["totalsItalic"])
        if fmt.get("totalsFontFamily"):
            tot["fontFamily"] = fmt["totalsFontFamily"]

        if is_matrix:
            rh = card("rowHeaders")
            _set(rh, "backColor", _fill(fmt.get("rowHeaderBackgroundColor", "")))
            _set(rh, "fontColor", _fill(fmt.get("rowHeaderTextColor", "")))
            if "rowHeaderFontSize" in fmt:
                rh["fontSize"] = fmt["rowHeaderFontSize"]
            if "rowHeaderFontBold" in fmt:
                rh["bold"] = bool(fmt["rowHeaderFontBold"])
            if "rowHeaderItalic" in fmt:
                rh["italic"] = bool(fmt["rowHeaderItalic"])
            if "rowHeaderAlignment" in fmt:
                rh["alignment"] = fmt["rowHeaderAlignment"]
            if "rowHeaderStepped" in fmt:
                rh["stepped"] = bool(fmt["rowHeaderStepped"])
            if fmt.get("rowHeaderFontFamily"):
                rh["fontFamily"] = fmt["rowHeaderFontFamily"]
            st = card("subTotals")
            if "showSubtotals" in fmt:
                st["rowSubtotals"] = bool(fmt["showSubtotals"])
            if "columnSubtotals" in fmt:
                st["columnSubtotals"] = bool(fmt["columnSubtotals"])
            _set(st, "backColor", _fill(fmt.get("subtotalsBackgroundColor", "")))
            if "subtotalsFontBold" in fmt:
                st["bold"] = bool(fmt["subtotalsFontBold"])
        # valuesAlignment / cellPadding have no clean global card and are omitted.

    # ---- Card ---- #
    elif app_key in _CARD:
        lab = card("labels")
        _set(lab, "color", _fill(fmt.get("valueColor", "")))
        if "valueFontSize" in fmt:
            lab["fontSize"] = fmt["valueFontSize"]
        if "valueFontBold" in fmt:
            lab["bold"] = bool(fmt["valueFontBold"])
        cl = card("categoryLabels")
        _set(cl, "color", _fill(fmt.get("labelColor", "")))
        if "labelFontSize" in fmt:
            cl["fontSize"] = fmt["labelFontSize"]
        bg = _fill(fmt.get("backgroundColor", ""))
        if bg is not None:
            card("background").update({"show": True, "color": bg})
        if "backgroundBorder" in fmt:
            card("border")["show"] = bool(fmt["backgroundBorder"])

    # ---- Multi-row card ---- #
    elif app_key in _MULTIROW:
        dl = card("dataLabels")
        _set(dl, "color", _fill(fmt.get("valueColor", "")))
        if "valueFontSize" in fmt:
            dl["fontSize"] = fmt["valueFontSize"]
        if "valueFontBold" in fmt:
            dl["bold"] = bool(fmt["valueFontBold"])
        cl = card("categoryLabels")
        _set(cl, "color", _fill(fmt.get("labelColor", "")))
        if "labelFontSize" in fmt:
            cl["fontSize"] = fmt["labelFontSize"]
        bg = _fill(fmt.get("backgroundColor", ""))
        if bg is not None:
            card("background").update({"show": True, "color": bg})
        if "backgroundBorder" in fmt:
            card("border")["show"] = bool(fmt["backgroundBorder"])

    # ---- KPI: indicator / goal / trend / status ---- #
    elif app_key in _KPI:
        ind = card("indicator")
        _set(ind, "fontColor", _fill(fmt.get("indicatorFontColor", "")))
        if "indicatorFontSize" in fmt:
            ind["fontSize"] = fmt["indicatorFontSize"]
        if "indicatorBold" in fmt:
            ind["bold"] = bool(fmt["indicatorBold"])
        goals = card("goals")
        if "showGoal" in fmt:
            goals["showGoal"] = bool(fmt["showGoal"])
        _set(goals, "goalFontColor", _fill(fmt.get("goalFontColor", "")))
        if "goalFontSize" in fmt:
            goals["fontSize"] = fmt["goalFontSize"]
        if "trendlineShow" in fmt:
            card("trendline")["show"] = bool(fmt["trendlineShow"])
        status = card("status")
        _set(status, "goodColor", _fill(fmt.get("statusGoodColor", "")))
        _set(status, "badColor", _fill(fmt.get("statusBadColor", "")))

    # ---- Slicer: header + items ---- #
    elif app_key in _SLICER:
        hdr = card("header")
        if "headerShow" in fmt:
            hdr["show"] = bool(fmt["headerShow"])
        _set(hdr, "fontColor", _fill(fmt.get("headerFontColor", "")))
        _set(hdr, "background", _fill(fmt.get("headerBackground", "")))
        if "headerTextSize" in fmt:
            hdr["textSize"] = fmt["headerTextSize"]
        if "headerBold" in fmt:
            hdr["bold"] = bool(fmt["headerBold"])
        it = card("items")
        _set(it, "fontColor", _fill(fmt.get("itemsFontColor", "")))
        _set(it, "background", _fill(fmt.get("itemsBackground", "")))
        if "itemsTextSize" in fmt:
            it["textSize"] = fmt["itemsTextSize"]
        if "itemsBold" in fmt:
            it["bold"] = bool(fmt["itemsBold"])

    # Drop any card left empty.
    return {k: v for k, v in cards.items() if v}


# Power BI's schema constrains card/text font sizes to this range.
FONT_SIZE_MIN, FONT_SIZE_MAX = 8, 60
_FONT_SIZE_KEYS = {"fontSize", "titleFontSize", "textSize"}


def clamp_font_size(value: Any) -> Any:
    """Clamp a font-size value into Power BI's allowed 8-60 range."""
    try:
        return max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, int(value)))
    except (TypeError, ValueError):
        return value


def _clamp_card_font_sizes(cards: Dict[str, Any]) -> None:
    for card_list in cards.values():
        if isinstance(card_list, list):
            for entry in card_list:
                if isinstance(entry, dict):
                    for key in _FONT_SIZE_KEYS & set(entry):
                        entry[key] = clamp_font_size(entry[key])


def _style_to_cards(app_key: str, style_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Turn one internal ``"*"`` style object into a dict of Power BI cards."""
    # Translated formatting is the lowest priority; explicit cards win.
    merged: Dict[str, Any] = {
        name: dict(props) for name, props in _translate_formatting(app_key, style_obj.get("formatting", {})).items()
    }
    for name, value in style_obj.items():
        if name == "formatting":
            continue
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
            merged.setdefault(name, {})
            if isinstance(merged[name], dict):
                merged[name].update(value[0])
            else:
                merged[name] = value
        else:
            merged[name] = value  # multi-entry ($id) or unusual: pass through
    # Wrap plain dict cards as single-item arrays, as Power BI expects.
    cards: Dict[str, Any] = {}
    for name, value in merged.items():
        cards[name] = [value] if isinstance(value, dict) else value
    _clamp_card_font_sizes(cards)
    return cards


def build_visual_styles(visual_styles: Dict[str, Any]) -> Dict[str, Any]:
    """Convert the app's ``visual_styles`` into a Power BI ``visualStyles`` dict.

    Input shape: ``{app_visual_key: {stylePreset: {"formatting": {...}, <cards>}}}``.
    Output shape: ``{pbi_visual_name: {stylePreset: {<cardName>: [ {..} ]}}}``.
    """
    result: Dict[str, Any] = {}
    for app_key, presets in (visual_styles or {}).items():
        pbi_name = VISUAL_NAME_MAP.get(app_key, app_key)
        out_presets = result.setdefault(pbi_name, {})
        for preset_name, style_obj in (presets or {}).items():
            if not isinstance(style_obj, dict):
                continue
            cards = _style_to_cards(app_key, style_obj)
            if preset_name in out_presets and isinstance(out_presets[preset_name], dict):
                # e.g. matrix + pivotTable both map to pivotTable: merge cards.
                out_presets[preset_name].update(cards)
            else:
                out_presets[preset_name] = cards
        if not out_presets:
            result.pop(pbi_name, None)
    return result


# --------------------------------------------------------------------------- #
# Import: real Power BI cards -> the app's internal formatting
# --------------------------------------------------------------------------- #
INVERSE_NAME_MAP = {pbi: app for app, pbi in VISUAL_NAME_MAP.items()}
_GRIDLINE_STYLE_INV = {v: k for k, v in _GRIDLINE_STYLE.items()}


def _hex(card: Dict[str, Any], prop: str) -> str | None:
    return _extract_solid_color(card.get(prop), "#000000") if prop in card else None


def _put(fmt: Dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        fmt[key] = value


def _axis_gridlines_inv(fmt: Dict[str, Any], c: Dict[str, Any]) -> None:
    if "gridlineShow" in c and not c["gridlineShow"]:
        fmt["gridlineStyle"] = "None"
    elif "gridlineStyle" in c:
        fmt["gridlineStyle"] = _GRIDLINE_STYLE_INV.get(c["gridlineStyle"], "Solid")
    elif c.get("gridlineShow"):
        fmt["gridlineStyle"] = "Solid"
    _put(fmt, "gridlineColor", _hex(c, "gridlineColor"))
    if "gridlineThickness" in c:
        fmt["gridlineThickness"] = c["gridlineThickness"]


# Per-family sets of cards that reconstruct the flat `formatting` dict (and are
# therefore removed from the passed-through cards). Everything else -- title,
# dropShadow, visualHeader, padding, and background/border except on cards --
# stays as a real card the generic-override section reads.
def _consumed_cards(app_key: str) -> set:
    if app_key in _CARTESIAN | _SCATTER:
        return {"categoryAxis", "valueAxis", "legend", "labels", "categoryLabels", "dataPoint"}
    if app_key in _PIE | _TREEMAP:
        return {"legend", "labels"}
    if app_key in _FUNNEL:
        return {"dataPoint", "labels"}
    if app_key in _GAUGE:
        return {"axis", "dataPoint", "target", "calloutValue"}
    if app_key in _TABLE_PLAIN | _MATRIX:
        return {"grid", "columnHeaders", "values", "total", "rowHeaders", "subTotals"}
    if app_key in _CARD:
        return {"labels", "categoryLabels", "background", "border"}
    if app_key in _MULTIROW:
        return {"dataLabels", "categoryLabels", "background", "border"}
    if app_key in _KPI:
        return {"indicator", "goals", "trendline", "status"}
    if app_key in _SLICER:
        return {"header", "items"}
    return set()


def _cards_to_formatting(app_key: str, cards: Dict[str, Any]) -> Dict[str, Any]:
    """Reconstruct the flat ``formatting`` dict from real Power BI cards."""
    fmt: Dict[str, Any] = {}

    def c(name: str) -> Dict[str, Any]:
        return _first(cards.get(name, []))

    if app_key in _CARTESIAN | _SCATTER:
        cat = c("categoryAxis")
        _put(fmt, "xAxisLabelColor", _hex(cat, "labelColor"))
        if "fontSize" in cat:
            fmt["xAxisLabelFontSize"] = cat["fontSize"]
        _put(fmt, "xAxisTitleColor", _hex(cat, "titleColor"))
        if "titleFontSize" in cat:
            fmt["xAxisTitleFontSize"] = cat["titleFontSize"]
        if "titleText" in cat:
            fmt["xAxisTitleText"] = cat["titleText"]
        val = c("valueAxis")
        _put(fmt, "yAxisLabelColor", _hex(val, "labelColor"))
        if "fontSize" in val:
            fmt["yAxisLabelFontSize"] = val["fontSize"]
        _put(fmt, "yAxisTitleColor", _hex(val, "titleColor"))
        if "titleFontSize" in val:
            fmt["yAxisTitleFontSize"] = val["titleFontSize"]
        if "titleText" in val:
            fmt["yAxisTitleText"] = val["titleText"]
        if "logAxisScale" in val:
            fmt["yAxisLogScale"] = bool(val["logAxisScale"])
        if "start" in val or "end" in val:
            fmt["yAxisSetRange"] = True
            if "start" in val:
                fmt["yAxisStart"] = val["start"]
            if "end" in val:
                fmt["yAxisEnd"] = val["end"]
        _axis_gridlines_inv(fmt, val)
        leg = c("legend")
        if "position" in leg:
            fmt["legendPosition"] = leg["position"]
        _put(fmt, "legendTextColor", _hex(leg, "labelColor"))
        if "fontSize" in leg:
            fmt["legendFontSize"] = leg["fontSize"]
        if "showTitle" in leg:
            fmt["legendShowTitle"] = bool(leg["showTitle"])
        if "titleText" in leg:
            fmt["legendTitleText"] = leg["titleText"]
        lab = c("categoryLabels") if app_key in _SCATTER else c("labels")
        _put(fmt, "dataLabelColor", _hex(lab, "color"))
        if "fontSize" in lab:
            fmt["dataLabelFontSize"] = lab["fontSize"]
        if "enableBackground" in lab:
            fmt["dataLabelBackground"] = bool(lab["enableBackground"])
        if "labelDisplayUnits" in lab:
            fmt["dataLabelDisplayUnits"] = str(lab["labelDisplayUnits"])
        if "labelPrecision" in lab:
            fmt["dataLabelPrecision"] = lab["labelPrecision"]
        if "labelPosition" in lab:
            fmt["dataLabelPosition"] = lab["labelPosition"]
        if app_key == "waterfallChart":
            sc = c("sentimentColors")
            _put(fmt, "defaultColor", _hex(sc, "increaseFill"))
            _put(fmt, "decreaseColor", _hex(sc, "decreaseFill"))
            _put(fmt, "totalColor", _hex(sc, "totalFill"))
        else:
            _put(fmt, "defaultColor", _hex(c("dataPoint"), "defaultColor"))

    elif app_key in _PIE | _TREEMAP:
        leg = c("legend")
        if "position" in leg:
            fmt["legendPosition"] = leg["position"]
        _put(fmt, "legendTextColor", _hex(leg, "labelColor"))
        if "fontSize" in leg:
            fmt["legendFontSize"] = leg["fontSize"]
        lab = c("labels")
        if "show" in lab:
            fmt["showDataLabels"] = bool(lab["show"])
        _put(fmt, "dataLabelColor", _hex(lab, "color"))
        if "fontSize" in lab:
            fmt["dataLabelFontSize"] = lab["fontSize"]

    elif app_key in _FUNNEL:
        _put(fmt, "barColor", _hex(c("dataPoint"), "defaultColor"))
        lab = c("labels")
        if "show" in lab:
            fmt["showDataLabels"] = bool(lab["show"])
        _put(fmt, "dataLabelColor", _hex(lab, "color"))
        if "fontSize" in lab:
            fmt["dataLabelFontSize"] = lab["fontSize"]

    elif app_key in _GAUGE:
        ax = c("axis")
        for src, dst in (("min", "minValue"), ("max", "maxValue"), ("target", "targetValue")):
            if src in ax:
                fmt[dst] = ax[src]
        _put(fmt, "fillColor", _hex(c("dataPoint"), "fill"))
        _put(fmt, "targetColor", _hex(c("target"), "color"))
        co = c("calloutValue")
        if "show" in co:
            fmt["showCallout"] = bool(co["show"])
        _put(fmt, "calloutColor", _hex(co, "color"))

    elif app_key in _TABLE_PLAIN | _MATRIX:
        grid = c("grid")
        if "gridHorizontal" in grid:
            fmt["gridlineStyle"] = "Solid" if grid["gridHorizontal"] else "None"
        _put(fmt, "gridlineColor", _hex(grid, "gridHorizontalColor"))
        if "gridHorizontalWeight" in grid:
            fmt["gridlineThickness"] = grid["gridHorizontalWeight"]
        if "rowPadding" in grid:
            fmt["rowSpacing"] = grid["rowPadding"]
        _put(fmt, "gridOutlineColor", _hex(grid, "outlineColor"))
        if "outlineWeight" in grid:
            fmt["gridOutlineWeight"] = grid["outlineWeight"]
        ch = c("columnHeaders")
        _put(fmt, "columnHeaderBackgroundColor", _hex(ch, "backColor"))
        _put(fmt, "columnHeaderTextColor", _hex(ch, "fontColor"))
        if "fontSize" in ch:
            fmt["columnHeaderFontSize"] = ch["fontSize"]
        if "bold" in ch:
            fmt["columnHeaderFontBold"] = bool(ch["bold"])
        if "italic" in ch:
            fmt["columnHeaderItalic"] = bool(ch["italic"])
        if "alignment" in ch:
            fmt["columnHeaderAlignment"] = ch["alignment"]
        if "fontFamily" in ch:
            fmt["columnHeaderFontFamily"] = ch["fontFamily"]
        if "wordWrap" in ch:
            fmt["columnHeaderWordWrap"] = bool(ch["wordWrap"])
        vals = c("values")
        _put(fmt, "valuesTextColor", _hex(vals, "fontColor"))
        if "fontSize" in vals:
            fmt["valuesFontSize"] = vals["fontSize"]
        if "italic" in vals:
            fmt["valuesItalic"] = bool(vals["italic"])
        if "fontFamily" in vals:
            fmt["valuesFontFamily"] = vals["fontFamily"]
        if "wordWrap" in vals:
            fmt["valuesWordWrap"] = bool(vals["wordWrap"])
        if "backColorSecondary" in vals:
            fmt["bandedRows"] = True
            _put(fmt, "alternateRowColor", _hex(vals, "backColorSecondary"))
            _put(fmt, "valuesBackgroundColor", _hex(vals, "backColorPrimary"))
        else:
            _put(fmt, "valuesBackgroundColor", _hex(vals, "backColor"))
        tot = c("total")
        if "totals" in tot:
            fmt["showTotals"] = bool(tot["totals"])
        _put(fmt, "totalsBackgroundColor", _hex(tot, "backColor"))
        _put(fmt, "totalsTextColor", _hex(tot, "fontColor"))
        if "bold" in tot:
            fmt["totalsFontBold"] = bool(tot["bold"])
        if "italic" in tot:
            fmt["totalsItalic"] = bool(tot["italic"])
        if "fontFamily" in tot:
            fmt["totalsFontFamily"] = tot["fontFamily"]
        if app_key in _MATRIX:
            rh = c("rowHeaders")
            _put(fmt, "rowHeaderBackgroundColor", _hex(rh, "backColor"))
            _put(fmt, "rowHeaderTextColor", _hex(rh, "fontColor"))
            if "fontSize" in rh:
                fmt["rowHeaderFontSize"] = rh["fontSize"]
            if "bold" in rh:
                fmt["rowHeaderFontBold"] = bool(rh["bold"])
            if "italic" in rh:
                fmt["rowHeaderItalic"] = bool(rh["italic"])
            if "alignment" in rh:
                fmt["rowHeaderAlignment"] = rh["alignment"]
            if "stepped" in rh:
                fmt["rowHeaderStepped"] = bool(rh["stepped"])
            if "fontFamily" in rh:
                fmt["rowHeaderFontFamily"] = rh["fontFamily"]
            st = c("subTotals")
            if "rowSubtotals" in st:
                fmt["showSubtotals"] = bool(st["rowSubtotals"])
            if "columnSubtotals" in st:
                fmt["columnSubtotals"] = bool(st["columnSubtotals"])
            _put(fmt, "subtotalsBackgroundColor", _hex(st, "backColor"))
            if "bold" in st:
                fmt["subtotalsFontBold"] = bool(st["bold"])

    elif app_key in _CARD | _MULTIROW:
        value_card = c("dataLabels") if app_key in _MULTIROW else c("labels")
        _put(fmt, "valueColor", _hex(value_card, "color"))
        if "fontSize" in value_card:
            fmt["valueFontSize"] = value_card["fontSize"]
        if "bold" in value_card:
            fmt["valueFontBold"] = bool(value_card["bold"])
        cl = c("categoryLabels")
        _put(fmt, "labelColor", _hex(cl, "color"))
        if "fontSize" in cl:
            fmt["labelFontSize"] = cl["fontSize"]
        _put(fmt, "backgroundColor", _hex(c("background"), "color"))
        border = c("border")
        if "show" in border:
            fmt["backgroundBorder"] = bool(border["show"])

    elif app_key in _KPI:
        ind = c("indicator")
        _put(fmt, "indicatorFontColor", _hex(ind, "fontColor"))
        if "fontSize" in ind:
            fmt["indicatorFontSize"] = ind["fontSize"]
        if "bold" in ind:
            fmt["indicatorBold"] = bool(ind["bold"])
        goals = c("goals")
        if "showGoal" in goals:
            fmt["showGoal"] = bool(goals["showGoal"])
        _put(fmt, "goalFontColor", _hex(goals, "goalFontColor"))
        if "fontSize" in goals:
            fmt["goalFontSize"] = goals["fontSize"]
        tl = c("trendline")
        if "show" in tl:
            fmt["trendlineShow"] = bool(tl["show"])
        status = c("status")
        _put(fmt, "statusGoodColor", _hex(status, "goodColor"))
        _put(fmt, "statusBadColor", _hex(status, "badColor"))

    elif app_key in _SLICER:
        hdr = c("header")
        if "show" in hdr:
            fmt["headerShow"] = bool(hdr["show"])
        _put(fmt, "headerFontColor", _hex(hdr, "fontColor"))
        _put(fmt, "headerBackground", _hex(hdr, "background"))
        if "textSize" in hdr:
            fmt["headerTextSize"] = hdr["textSize"]
        if "bold" in hdr:
            fmt["headerBold"] = bool(hdr["bold"])
        it = c("items")
        _put(fmt, "itemsFontColor", _hex(it, "fontColor"))
        _put(fmt, "itemsBackground", _hex(it, "background"))
        if "textSize" in it:
            fmt["itemsTextSize"] = it["textSize"]
        if "bold" in it:
            fmt["itemsBold"] = bool(it["bold"])

    return fmt


def import_visual_styles(raw_visual_styles: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Power BI ``visualStyles`` dict into the app's internal form.

    Inverse of :func:`build_visual_styles`: real cards for a customizable visual
    are reconstructed into a flat ``formatting`` block (so the editor's formatter
    panel repopulates), while generic cards (title, background, border, drop
    shadow, visual header, padding) pass through for the generic-override section.
    Power BI visual names are mapped back (pivotTable -> matrix, tableEx -> table).
    """
    from .gui.visual_formatting_config import is_visual_customizable

    result: Dict[str, Any] = {}
    for pbi_name, presets in (raw_visual_styles or {}).items():
        app_key = INVERSE_NAME_MAP.get(pbi_name, pbi_name)
        out: Dict[str, Any] = {}
        for preset_name, cards in (presets or {}).items():
            if not isinstance(cards, dict):
                out[preset_name] = cards
                continue
            if is_visual_customizable(app_key):
                consumed = _consumed_cards(app_key)
                style = {name: val for name, val in cards.items() if name not in consumed}
                fmt = _cards_to_formatting(app_key, cards)
                if fmt:
                    style["formatting"] = fmt
                out[preset_name] = style
            else:
                out[preset_name] = dict(cards)
        result[app_key] = out
    return result
