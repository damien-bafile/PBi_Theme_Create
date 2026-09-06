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

from typing import Any, Dict

from .model import _solid_color, is_valid_hex

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

        val = card("valueAxis")
        _set(val, "labelColor", _fill(fmt.get("yAxisLabelColor", "")))
        if "yAxisLabelFontSize" in fmt:
            val["fontSize"] = fmt["yAxisLabelFontSize"]
        _set(val, "titleColor", _fill(fmt.get("yAxisTitleColor", "")))
        if "yAxisTitleFontSize" in fmt:
            val["titleFontSize"] = fmt["yAxisTitleFontSize"]
        _axis_gridlines(val, fmt)

        leg = card("legend")
        if "legendPosition" in fmt:
            leg["position"] = fmt["legendPosition"]
        _set(leg, "labelColor", _fill(fmt.get("legendTextColor", "")))
        if "legendFontSize" in fmt:
            leg["fontSize"] = fmt["legendFontSize"]

        # Scatter has no `labels` card -- data labels live on `categoryLabels`.
        label_card = "categoryLabels" if app_key in _SCATTER else "labels"
        lab = card(label_card)
        _set(lab, "color", _fill(fmt.get("dataLabelColor", "")))
        if "dataLabelFontSize" in fmt:
            lab["fontSize"] = fmt["dataLabelFontSize"]
        if app_key not in _SCATTER and "dataLabelBackground" in fmt:
            lab["enableBackground"] = bool(fmt["dataLabelBackground"])
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

        ch = card("columnHeaders")
        _set(ch, "backColor", _fill(fmt.get("columnHeaderBackgroundColor", "")))
        _set(ch, "fontColor", _fill(fmt.get("columnHeaderTextColor", "")))
        if "columnHeaderFontSize" in fmt:
            ch["fontSize"] = fmt["columnHeaderFontSize"]
        if "columnHeaderFontBold" in fmt:
            ch["bold"] = bool(fmt["columnHeaderFontBold"])
        if "columnHeaderAlignment" in fmt:
            ch["alignment"] = fmt["columnHeaderAlignment"]

        vals = card("values")
        _set(vals, "backColor", _fill(fmt.get("valuesBackgroundColor", "")))
        _set(vals, "fontColor", _fill(fmt.get("valuesTextColor", "")))
        if "valuesFontSize" in fmt:
            vals["fontSize"] = fmt["valuesFontSize"]

        tot = card("total")
        if "showTotals" in fmt:
            tot["totals"] = bool(fmt["showTotals"])
        _set(tot, "backColor", _fill(fmt.get("totalsBackgroundColor", "")))
        _set(tot, "fontColor", _fill(fmt.get("totalsTextColor", "")))
        if "totalsFontBold" in fmt:
            tot["bold"] = bool(fmt["totalsFontBold"])

        if is_matrix:
            rh = card("rowHeaders")
            _set(rh, "backColor", _fill(fmt.get("rowHeaderBackgroundColor", "")))
            _set(rh, "fontColor", _fill(fmt.get("rowHeaderTextColor", "")))
            if "rowHeaderFontSize" in fmt:
                rh["fontSize"] = fmt["rowHeaderFontSize"]
            if "rowHeaderFontBold" in fmt:
                rh["bold"] = bool(fmt["rowHeaderFontBold"])
            st = card("subTotals")
            if "showSubtotals" in fmt:
                st["rowSubtotals"] = bool(fmt["showSubtotals"])
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
