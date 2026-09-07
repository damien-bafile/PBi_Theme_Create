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
    "basicShape": "shape",
    "azureMapVisual": "azureMap",
    "smartNarrative": "aiNarratives",
}

# Families (by app key) that share a translation.
_CARTESIAN = {
    "barChart", "columnChart", "clusteredBarChart", "clusteredColumnChart",
    "hundredPercentStackedBarChart", "hundredPercentStackedColumnChart",
    "lineChart", "areaChart", "lineClusteredColumnComboChart",
    "lineStackedColumnComboChart", "ribbonChart", "waterfallChart",
}
_SCATTER = {"scatterChart"}
_ACTION_BUTTON = {"actionButton"}
_SHAPE_VIS = {"basicShape"}
_DECOMP = {"decompositionTreeVisual"}
_MAP = {"map", "filledMap"}
_SHAPE_MAP = {"shapeMap"}
_IMAGE = {"image"}
_TEXTBOX = {"textbox"}
_SMART_NARRATIVE = {"smartNarrative"}
# Cartesian visuals that have a `trend` card (waterfall & line+stacked combo don't).
_TREND_VISUALS = (_CARTESIAN | _SCATTER) - {"waterfallChart", "lineStackedColumnComboChart"}
# Cartesian visuals with a `smallMultiplesLayout` card (not waterfall or scatter).
_SMALL_MULTIPLES = _CARTESIAN - {"waterfallChart"}
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


def _state_entry(entries: Any, state: str) -> Dict[str, Any]:
    """Return the ``$id``-keyed state object (``default`` / ``hover`` ...) or ``{}``."""
    if isinstance(entries, list):
        for e in entries:
            if isinstance(e, dict) and e.get("$id") == state:
                return e
    return {}


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

        # Reference line (all cartesian have y1AxisReferenceLine).
        if "refLineShow" in fmt:
            ref = card("y1AxisReferenceLine")
            ref["show"] = bool(fmt["refLineShow"])
            if "refLineValue" in fmt:
                ref["value"] = fmt["refLineValue"]
            _set(ref, "lineColor", _fill(fmt.get("refLineColor", "")))
        # Trend line (not on waterfall / line+stacked combo).
        if "trendShow" in fmt and app_key in _TREND_VISUALS:
            tr = card("trend")
            tr["show"] = bool(fmt["trendShow"])
            _set(tr, "lineColor", _fill(fmt.get("trendColor", "")))
        # Scatter markers / bubbles.
        if app_key in _SCATTER:
            if "bubbleSize" in fmt:
                card("bubbles")["bubbleSize"] = fmt["bubbleSize"]
            mb = _fill(fmt.get("markerBorderColor", ""))
            if mb is not None:
                card("markers").update({"borderShow": True, "borderColor": mb})
        # Small multiples layout (cartesian, excluding waterfall / scatter).
        if app_key in _SMALL_MULTIPLES:
            sm = card("smallMultiplesLayout")
            if "smColumnCount" in fmt:
                sm["columnCount"] = fmt["smColumnCount"]
            if "smRowCount" in fmt:
                sm["rowCount"] = fmt["smRowCount"]
            _set(sm, "gridLineColor", _fill(fmt.get("smGridlineColor", "")))
            _set(sm, "backgroundColor", _fill(fmt.get("smBackgroundColor", "")))
        # Plot area transparency (image-only card otherwise).
        if "plotAreaTransparency" in fmt:
            card("plotArea")["transparency"] = fmt["plotAreaTransparency"]
        # Ratio line (scatter only).
        if app_key in _SCATTER and "ratioLineShow" in fmt:
            rl = card("ratioLine")
            rl["show"] = bool(fmt["ratioLineShow"])
            _set(rl, "lineColor", _fill(fmt.get("ratioLineColor", "")))

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
        # Slices (pie/donut only -- treemap has no slices card).
        if app_key in _PIE:
            sl = card("slices")
            if "sliceStartAngle" in fmt:
                sl["startAngle"] = fmt["sliceStartAngle"]
            if "sliceInnerRadius" in fmt:
                sl["innerRadiusRatio"] = fmt["sliceInnerRadius"]

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
        if "gridTextSize" in fmt:
            grid["textSize"] = fmt["gridTextSize"]

        ch = card("columnHeaders")
        _set(ch, "backColor", _fill(fmt.get("columnHeaderBackgroundColor", "")))
        _set(ch, "fontColor", _fill(fmt.get("columnHeaderTextColor", "")))
        if "columnHeaderFontSize" in fmt:
            ch["fontSize"] = fmt["columnHeaderFontSize"]
        if "columnHeaderFontBold" in fmt:
            ch["bold"] = bool(fmt["columnHeaderFontBold"])
        if "columnHeaderItalic" in fmt:
            ch["italic"] = bool(fmt["columnHeaderItalic"])
        if "columnHeaderUnderline" in fmt:
            ch["underline"] = bool(fmt["columnHeaderUnderline"])
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
        if "valuesFontBold" in fmt:
            vals["bold"] = bool(fmt["valuesFontBold"])
        if "valuesItalic" in fmt:
            vals["italic"] = bool(fmt["valuesItalic"])
        if "valuesUnderline" in fmt:
            vals["underline"] = bool(fmt["valuesUnderline"])
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
        if "totalsFontSize" in fmt:
            tot["fontSize"] = fmt["totalsFontSize"]
        if "totalsFontBold" in fmt:
            tot["bold"] = bool(fmt["totalsFontBold"])
        if "totalsItalic" in fmt:
            tot["italic"] = bool(fmt["totalsItalic"])
        if "totalsUnderline" in fmt:
            tot["underline"] = bool(fmt["totalsUnderline"])
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
            if "rowHeaderUnderline" in fmt:
                rh["underline"] = bool(fmt["rowHeaderUnderline"])
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
            _set(st, "fontColor", _fill(fmt.get("subtotalsTextColor", "")))
            if "subtotalsFontSize" in fmt:
                st["fontSize"] = fmt["subtotalsFontSize"]
            if "subtotalsFontBold" in fmt:
                st["bold"] = bool(fmt["subtotalsFontBold"])
            if "subtotalsItalic" in fmt:
                st["italic"] = bool(fmt["subtotalsItalic"])
            if "subtotalsUnderline" in fmt:
                st["underline"] = bool(fmt["subtotalsUnderline"])
            if fmt.get("subtotalsFontFamily"):
                st["fontFamily"] = fmt["subtotalsFontFamily"]

        # Grand-total label (table) / apply-to-headers (matrix).
        if not is_matrix and fmt.get("totalsLabel"):
            tot["label"] = fmt["totalsLabel"]
        if is_matrix and "totalsApplyToHeaders" in fmt:
            tot["applyToHeaders"] = bool(fmt["totalsApplyToHeaders"])

        # Data bars (columnFormatting default -- applies to numeric value columns).
        # The dataBars object requires both reverseDirection and hideText.
        if fmt.get("dataBarsShow"):
            db: Dict[str, Any] = {
                "reverseDirection": bool(fmt.get("dataBarsReverse", False)),
                "hideText": bool(fmt.get("dataBarsHideText", False)),
            }
            _set(db, "positiveColor", _fill(fmt.get("dataBarsPositiveColor", "")))
            _set(db, "negativeColor", _fill(fmt.get("dataBarsNegativeColor", "")))
            _set(db, "axisColor", _fill(fmt.get("dataBarsAxisColor", "")))
            cf = card("columnFormatting")
            cf["dataBars"] = db
            cf["styleValues"] = True

        # Column sizing.
        if "columnAutoSize" in fmt:
            card("columnHeaders")["autoSizeColumnWidth"] = bool(fmt["columnAutoSize"])
        if "defaultColumnWidth" in fmt:
            card("columnWidth")["value"] = fmt["defaultColumnWidth"]

        # Sparklines (in-cell mini charts).
        if fmt.get("sparklineType") or fmt.get("sparklineColor") or fmt.get("sparklineMarkerColor"):
            sp = card("sparklines")
            if fmt.get("sparklineType"):
                sp["chartType"] = fmt["sparklineType"]
            _set(sp, "dataColor", _fill(fmt.get("sparklineColor", "")))
            _set(sp, "markerColor", _fill(fmt.get("sparklineMarkerColor", "")))

        # Built-in table style preset.
        if fmt.get("stylePreset"):
            card("stylePreset")["name"] = fmt["stylePreset"]

        # Blank rows (matrix only).
        if is_matrix:
            if "blankRowsShow" in fmt or fmt.get("blankRowColor") or fmt.get("blankRowBorderColor"):
                br = card("blankRows")
                if "blankRowsShow" in fmt:
                    br["showBlankRows"] = bool(fmt["blankRowsShow"])
                _set(br, "blankRowColor", _fill(fmt.get("blankRowColor", "")))
                bc = _fill(fmt.get("blankRowBorderColor", ""))
                if bc is not None:
                    br["borderColor"] = bc
                    br["showBorder"] = True
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
        _set(card("slider"), "color", _fill(fmt.get("sliderColor", "")))
        _set(card("selectionIcon"), "color", _fill(fmt.get("selectionColor", "")))
        sb = card("searchBox")
        _set(sb, "background", _fill(fmt.get("searchBackground", "")))
        _set(sb, "borderColor", _fill(fmt.get("searchBorderColor", "")))
        dt = card("date")
        _set(dt, "fontColor", _fill(fmt.get("dateFontColor", "")))
        _set(dt, "background", _fill(fmt.get("dateBackground", "")))
        if "dateTextSize" in fmt:
            dt["textSize"] = fmt["dateTextSize"]
        ni = card("numericInputStyle")
        _set(ni, "fontColor", _fill(fmt.get("numericFontColor", "")))
        _set(ni, "background", _fill(fmt.get("numericBackground", "")))
        if "numericTextSize" in fmt:
            ni["textSize"] = fmt["numericTextSize"]
        dd = card("dropdown")
        _set(dd, "iconColor", _fill(fmt.get("dropdownIconColor", "")))
        _set(dd, "borderColor", _fill(fmt.get("dropdownBorderColor", "")))

    # ---- Action button: fill / text / outline / icon / glow / shadow ---- #
    elif app_key in _ACTION_BUTTON:
        # Fill & text support a `hover` state: emit a `$id`-keyed array when set,
        # otherwise the simple single-object card (so the common case round-trips
        # unchanged).
        fill_default = _fill(fmt.get("buttonFillColor", ""))
        fill_hover = _fill(fmt.get("buttonHoverFillColor", ""))
        if fill_hover is not None:
            base = {"$id": "default"}
            _set(base, "fillColor", fill_default)
            cards["fill"] = [base, {"$id": "hover", "fillColor": fill_hover}]
        else:
            _set(card("fill"), "fillColor", fill_default)
        text_default = _fill(fmt.get("buttonTextColor", ""))
        text_hover = _fill(fmt.get("buttonHoverTextColor", ""))
        if text_hover is not None:
            base = {"$id": "default"}
            _set(base, "fontColor", text_default)
            cards["text"] = [base, {"$id": "hover", "fontColor": text_hover}]
        else:
            _set(card("text"), "fontColor", text_default)
        out = card("outline")
        _set(out, "lineColor", _fill(fmt.get("buttonOutlineColor", "")))
        if "buttonOutlineWeight" in fmt:
            out["weight"] = fmt["buttonOutlineWeight"]
        ic = card("icon")
        if fmt.get("buttonIconShape"):
            ic["shapeType"] = fmt["buttonIconShape"]
        _set(ic, "lineColor", _fill(fmt.get("buttonIconColor", "")))
        if "buttonIconSize" in fmt:
            ic["iconSize"] = fmt["buttonIconSize"]
        gl = card("glow")
        if "buttonGlowShow" in fmt:
            gl["show"] = bool(fmt["buttonGlowShow"])
        _set(gl, "color", _fill(fmt.get("buttonGlowColor", "")))
        sh = card("shadow")
        if "buttonShadowShow" in fmt:
            sh["show"] = bool(fmt["buttonShadowShow"])
        _set(sh, "color", _fill(fmt.get("buttonShadowColor", "")))

    # ---- Basic shape: fill + outline ---- #
    elif app_key in _SHAPE_VIS:
        _set(card("fill"), "fillColor", _fill(fmt.get("shapeFillColor", "")))
        out = card("outline")
        _set(out, "lineColor", _fill(fmt.get("shapeOutlineColor", "")))
        if "shapeOutlineWeight" in fmt:
            out["weight"] = fmt["shapeOutlineWeight"]

    # ---- Decomposition tree: level header + data labels ---- #
    elif app_key in _DECOMP:
        lh = card("levelHeader")
        _set(lh, "levelHeaderBackgroundColor", _fill(fmt.get("levelHeaderBg", "")))
        _set(lh, "levelTitleFontColor", _fill(fmt.get("levelTitleColor", "")))
        _set(card("dataLabels"), "dataLabelFontColor", _fill(fmt.get("treeDataLabelColor", "")))

    # ---- Map / filled map: data point + category labels + style + controls ---- #
    elif app_key in _MAP:
        _set(card("dataPoint"), "defaultColor", _fill(fmt.get("mapDataColor", "")))
        if app_key == "map":  # only the base map's categoryLabels card has a colour
            _set(card("categoryLabels"), "color", _fill(fmt.get("mapLabelColor", "")))
        if app_key == "filledMap":  # region borders
            _set(card("stroke"), "strokeColor", _fill(fmt.get("mapStrokeColor", "")))
        ms = card("mapStyles")
        if fmt.get("mapTheme"):
            ms["mapTheme"] = fmt["mapTheme"]
        if "mapShowLabels" in fmt:
            ms["showLabels"] = bool(fmt["mapShowLabels"])
        mc = card("mapControls")
        if "mapAutoZoom" in fmt:
            mc["autoZoom"] = bool(fmt["mapAutoZoom"])
        if "mapShowZoom" in fmt:
            mc["showZoomButtons"] = bool(fmt["mapShowZoom"])

    # ---- Text box: text colour / size / font ---- #
    elif app_key in _TEXTBOX:
        txt = card("text")
        _set(txt, "color", _fill(fmt.get("textColor", "")))
        if "textFontSize" in fmt:
            txt["fontSize"] = fmt["textFontSize"]
        if fmt.get("textFontFamily"):
            txt["fontFamily"] = fmt["textFontFamily"]

    # ---- Smart narrative (aiNarratives): generated-text styling ---- #
    elif app_key in _SMART_NARRATIVE:
        txt = card("text")
        _set(txt, "fontColor", _fill(fmt.get("narrativeTextColor", "")))
        if "narrativeFontSize" in fmt:
            txt["fontSize"] = fmt["narrativeFontSize"]
        if fmt.get("narrativeFontFamily"):
            txt["fontFamily"] = fmt["narrativeFontFamily"]
        if fmt.get("narrativeAlignment"):
            txt["textAlignment"] = fmt["narrativeAlignment"]

    # ---- Shape map: default colours ---- #
    elif app_key in _SHAPE_MAP:
        dc = card("defaultColors")
        _set(dc, "defaultColor", _fill(fmt.get("shapeMapColor", "")))
        _set(dc, "borderColor", _fill(fmt.get("shapeMapBorderColor", "")))

    # ---- Image: scaling mode ---- #
    elif app_key in _IMAGE:
        if fmt.get("imageScaling"):
            card("imageScaling")["imageScalingType"] = fmt["imageScaling"]

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
    # A card may be a single dict or, for state-keyed cards (button hover), a list.
    merged: Dict[str, Any] = {}
    for name, props in _translate_formatting(app_key, style_obj.get("formatting", {})).items():
        merged[name] = [dict(p) for p in props] if isinstance(props, list) else dict(props)
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
        return {"categoryAxis", "valueAxis", "legend", "labels", "categoryLabels", "dataPoint",
                "y1AxisReferenceLine", "trend", "sentimentColors", "bubbles", "markers",
                "smallMultiplesLayout", "plotArea", "ratioLine"}
    if app_key in _PIE | _TREEMAP:
        return {"legend", "labels", "slices"}
    if app_key in _FUNNEL:
        return {"dataPoint", "labels"}
    if app_key in _GAUGE:
        return {"axis", "dataPoint", "target", "calloutValue"}
    if app_key in _TABLE_PLAIN | _MATRIX:
        return {"grid", "columnHeaders", "values", "total", "rowHeaders", "subTotals",
                "columnFormatting", "columnWidth", "sparklines", "stylePreset", "blankRows"}
    if app_key in _CARD:
        return {"labels", "categoryLabels", "background", "border"}
    if app_key in _MULTIROW:
        return {"dataLabels", "categoryLabels", "background", "border"}
    if app_key in _KPI:
        return {"indicator", "goals", "trendline", "status"}
    if app_key in _SLICER:
        return {"header", "items", "slider", "selectionIcon", "searchBox",
                "date", "numericInputStyle", "dropdown"}
    if app_key in _ACTION_BUTTON:
        return {"fill", "text", "outline", "icon", "glow", "shadow"}
    if app_key in _SHAPE_VIS:
        return {"fill", "outline"}
    if app_key in _DECOMP:
        return {"levelHeader", "dataLabels"}
    if app_key in _MAP:
        return {"dataPoint", "categoryLabels", "stroke", "mapStyles", "mapControls"}
    if app_key in _SHAPE_MAP:
        return {"defaultColors"}
    if app_key in _IMAGE:
        return {"imageScaling"}
    if app_key in _TEXTBOX | _SMART_NARRATIVE:
        return {"text"}
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
        ref = c("y1AxisReferenceLine")
        if "show" in ref:
            fmt["refLineShow"] = bool(ref["show"])
        if "value" in ref:
            fmt["refLineValue"] = ref["value"]
        _put(fmt, "refLineColor", _hex(ref, "lineColor"))
        tr = c("trend")
        if "show" in tr:
            fmt["trendShow"] = bool(tr["show"])
        _put(fmt, "trendColor", _hex(tr, "lineColor"))
        if app_key in _SCATTER:
            bub = c("bubbles")
            if "bubbleSize" in bub:
                fmt["bubbleSize"] = bub["bubbleSize"]
            _put(fmt, "markerBorderColor", _hex(c("markers"), "borderColor"))
        if app_key in _SMALL_MULTIPLES:
            sm = c("smallMultiplesLayout")
            if "columnCount" in sm:
                fmt["smColumnCount"] = sm["columnCount"]
            if "rowCount" in sm:
                fmt["smRowCount"] = sm["rowCount"]
            _put(fmt, "smGridlineColor", _hex(sm, "gridLineColor"))
            _put(fmt, "smBackgroundColor", _hex(sm, "backgroundColor"))
        pa = c("plotArea")
        if "transparency" in pa:
            fmt["plotAreaTransparency"] = pa["transparency"]
        if app_key in _SCATTER:
            rl = c("ratioLine")
            if "show" in rl:
                fmt["ratioLineShow"] = bool(rl["show"])
            _put(fmt, "ratioLineColor", _hex(rl, "lineColor"))

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
        if app_key in _PIE:
            sl = c("slices")
            if "startAngle" in sl:
                fmt["sliceStartAngle"] = sl["startAngle"]
            if "innerRadiusRatio" in sl:
                fmt["sliceInnerRadius"] = sl["innerRadiusRatio"]

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
        if "textSize" in grid:
            fmt["gridTextSize"] = grid["textSize"]
        ch = c("columnHeaders")
        _put(fmt, "columnHeaderBackgroundColor", _hex(ch, "backColor"))
        _put(fmt, "columnHeaderTextColor", _hex(ch, "fontColor"))
        if "fontSize" in ch:
            fmt["columnHeaderFontSize"] = ch["fontSize"]
        if "bold" in ch:
            fmt["columnHeaderFontBold"] = bool(ch["bold"])
        if "italic" in ch:
            fmt["columnHeaderItalic"] = bool(ch["italic"])
        if "underline" in ch:
            fmt["columnHeaderUnderline"] = bool(ch["underline"])
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
        if "bold" in vals:
            fmt["valuesFontBold"] = bool(vals["bold"])
        if "italic" in vals:
            fmt["valuesItalic"] = bool(vals["italic"])
        if "underline" in vals:
            fmt["valuesUnderline"] = bool(vals["underline"])
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
        if "fontSize" in tot:
            fmt["totalsFontSize"] = tot["fontSize"]
        if "bold" in tot:
            fmt["totalsFontBold"] = bool(tot["bold"])
        if "italic" in tot:
            fmt["totalsItalic"] = bool(tot["italic"])
        if "underline" in tot:
            fmt["totalsUnderline"] = bool(tot["underline"])
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
            if "underline" in rh:
                fmt["rowHeaderUnderline"] = bool(rh["underline"])
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
            _put(fmt, "subtotalsTextColor", _hex(st, "fontColor"))
            if "fontSize" in st:
                fmt["subtotalsFontSize"] = st["fontSize"]
            if "bold" in st:
                fmt["subtotalsFontBold"] = bool(st["bold"])
            if "italic" in st:
                fmt["subtotalsItalic"] = bool(st["italic"])
            if "underline" in st:
                fmt["subtotalsUnderline"] = bool(st["underline"])
            if "fontFamily" in st:
                fmt["subtotalsFontFamily"] = st["fontFamily"]
            if "applyToHeaders" in tot:
                fmt["totalsApplyToHeaders"] = bool(tot["applyToHeaders"])
        if "label" in tot:
            fmt["totalsLabel"] = tot["label"]

        cf = c("columnFormatting")
        db = cf.get("dataBars") if isinstance(cf.get("dataBars"), dict) else None
        if db is not None:
            fmt["dataBarsShow"] = True
            _put(fmt, "dataBarsPositiveColor", _hex(db, "positiveColor"))
            _put(fmt, "dataBarsNegativeColor", _hex(db, "negativeColor"))
            _put(fmt, "dataBarsAxisColor", _hex(db, "axisColor"))
            if "hideText" in db:
                fmt["dataBarsHideText"] = bool(db["hideText"])
            if "reverseDirection" in db:
                fmt["dataBarsReverse"] = bool(db["reverseDirection"])
        if "autoSizeColumnWidth" in ch:
            fmt["columnAutoSize"] = bool(ch["autoSizeColumnWidth"])
        cw = c("columnWidth")
        if "value" in cw:
            fmt["defaultColumnWidth"] = cw["value"]
        sp = c("sparklines")
        if "chartType" in sp:
            fmt["sparklineType"] = sp["chartType"]
        _put(fmt, "sparklineColor", _hex(sp, "dataColor"))
        _put(fmt, "sparklineMarkerColor", _hex(sp, "markerColor"))
        pre = c("stylePreset")
        if "name" in pre:
            fmt["stylePreset"] = pre["name"]
        if app_key in _MATRIX:
            br = c("blankRows")
            if "showBlankRows" in br:
                fmt["blankRowsShow"] = bool(br["showBlankRows"])
            _put(fmt, "blankRowColor", _hex(br, "blankRowColor"))
            _put(fmt, "blankRowBorderColor", _hex(br, "borderColor"))

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
        _put(fmt, "sliderColor", _hex(c("slider"), "color"))
        _put(fmt, "selectionColor", _hex(c("selectionIcon"), "color"))
        sb = c("searchBox")
        _put(fmt, "searchBackground", _hex(sb, "background"))
        _put(fmt, "searchBorderColor", _hex(sb, "borderColor"))
        dt = c("date")
        _put(fmt, "dateFontColor", _hex(dt, "fontColor"))
        _put(fmt, "dateBackground", _hex(dt, "background"))
        if "textSize" in dt:
            fmt["dateTextSize"] = dt["textSize"]
        ni = c("numericInputStyle")
        _put(fmt, "numericFontColor", _hex(ni, "fontColor"))
        _put(fmt, "numericBackground", _hex(ni, "background"))
        if "textSize" in ni:
            fmt["numericTextSize"] = ni["textSize"]
        dd = c("dropdown")
        _put(fmt, "dropdownIconColor", _hex(dd, "iconColor"))
        _put(fmt, "dropdownBorderColor", _hex(dd, "borderColor"))

    elif app_key in _ACTION_BUTTON:
        fill_entries = cards.get("fill", [])
        default_fill = _state_entry(fill_entries, "default") or _first(fill_entries)
        _put(fmt, "buttonFillColor", _hex(default_fill, "fillColor"))
        _put(fmt, "buttonHoverFillColor", _hex(_state_entry(fill_entries, "hover"), "fillColor"))
        text_entries = cards.get("text", [])
        default_text = _state_entry(text_entries, "default") or _first(text_entries)
        _put(fmt, "buttonTextColor", _hex(default_text, "fontColor"))
        _put(fmt, "buttonHoverTextColor", _hex(_state_entry(text_entries, "hover"), "fontColor"))
        out = c("outline")
        _put(fmt, "buttonOutlineColor", _hex(out, "lineColor"))
        if "weight" in out:
            fmt["buttonOutlineWeight"] = out["weight"]
        ic = c("icon")
        if "shapeType" in ic:
            fmt["buttonIconShape"] = ic["shapeType"]
        _put(fmt, "buttonIconColor", _hex(ic, "lineColor"))
        if "iconSize" in ic:
            fmt["buttonIconSize"] = ic["iconSize"]
        gl = c("glow")
        if "show" in gl:
            fmt["buttonGlowShow"] = bool(gl["show"])
        _put(fmt, "buttonGlowColor", _hex(gl, "color"))
        sh = c("shadow")
        if "show" in sh:
            fmt["buttonShadowShow"] = bool(sh["show"])
        _put(fmt, "buttonShadowColor", _hex(sh, "color"))

    elif app_key in _SHAPE_VIS:
        _put(fmt, "shapeFillColor", _hex(c("fill"), "fillColor"))
        out = c("outline")
        _put(fmt, "shapeOutlineColor", _hex(out, "lineColor"))
        if "weight" in out:
            fmt["shapeOutlineWeight"] = out["weight"]

    elif app_key in _DECOMP:
        lh = c("levelHeader")
        _put(fmt, "levelHeaderBg", _hex(lh, "levelHeaderBackgroundColor"))
        _put(fmt, "levelTitleColor", _hex(lh, "levelTitleFontColor"))
        _put(fmt, "treeDataLabelColor", _hex(c("dataLabels"), "dataLabelFontColor"))

    elif app_key in _MAP:
        _put(fmt, "mapDataColor", _hex(c("dataPoint"), "defaultColor"))
        _put(fmt, "mapLabelColor", _hex(c("categoryLabels"), "color"))
        if app_key == "filledMap":
            _put(fmt, "mapStrokeColor", _hex(c("stroke"), "strokeColor"))
        ms = c("mapStyles")
        if "mapTheme" in ms:
            fmt["mapTheme"] = ms["mapTheme"]
        if "showLabels" in ms:
            fmt["mapShowLabels"] = bool(ms["showLabels"])
        mc = c("mapControls")
        if "autoZoom" in mc:
            fmt["mapAutoZoom"] = bool(mc["autoZoom"])
        if "showZoomButtons" in mc:
            fmt["mapShowZoom"] = bool(mc["showZoomButtons"])

    elif app_key in _TEXTBOX:
        txt = c("text")
        _put(fmt, "textColor", _hex(txt, "color"))
        if "fontSize" in txt:
            fmt["textFontSize"] = txt["fontSize"]
        if "fontFamily" in txt:
            fmt["textFontFamily"] = txt["fontFamily"]

    elif app_key in _SMART_NARRATIVE:
        txt = c("text")
        _put(fmt, "narrativeTextColor", _hex(txt, "fontColor"))
        if "fontSize" in txt:
            fmt["narrativeFontSize"] = txt["fontSize"]
        if "fontFamily" in txt:
            fmt["narrativeFontFamily"] = txt["fontFamily"]
        if "textAlignment" in txt:
            fmt["narrativeAlignment"] = txt["textAlignment"]

    elif app_key in _SHAPE_MAP:
        dc = c("defaultColors")
        _put(fmt, "shapeMapColor", _hex(dc, "defaultColor"))
        _put(fmt, "shapeMapBorderColor", _hex(dc, "borderColor"))

    elif app_key in _IMAGE:
        img = c("imageScaling")
        if "imageScalingType" in img:
            fmt["imageScaling"] = img["imageScalingType"]

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
