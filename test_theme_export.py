#!/usr/bin/env python3
"""Regression test: exported themes use valid Power BI cards, not the app's
internal ``formatting`` block.

Checks the structural invariants that make a theme importable into Power BI
(verified against microsoft/powerbi-desktop-samples reportThemeSchema):
real card names, ``{solid:{color}}`` colours, correct visual-name mapping,
and font sizes within the 8-60 range. Runs head-less.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pbitheme.model import PowerBITheme
from pbitheme.theme_export import build_visual_styles, import_visual_styles


def _style(formatting=None, **cards):
    obj = {}
    if formatting:
        obj["formatting"] = formatting
    obj.update(cards)
    return {"*": obj}


def _is_solid(v):
    return isinstance(v, dict) and "solid" in v and "color" in v["solid"]


def main() -> int:
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    # 1) Chart formatting -> real cards, no `formatting` blob, solid colours.
    vs = build_visual_styles({
        "barChart": _style({
            "xAxisLabelColor": "#FF0000", "xAxisLabelFontSize": 12,
            "yAxisTitleColor": "#00FF00",
            "gridlineStyle": "Dashed", "gridlineColor": "#123456", "gridlineThickness": 2,
            "dataLabelColor": "#0000FF", "dataLabelBackground": True,
            "legendPosition": "Bottom", "legendTextColor": "#ABCDEF", "legendFontSize": 90,
        })
    })
    bar = vs["barChart"]["*"]
    check("formatting" not in bar, "barChart still exports a `formatting` card")
    check("categoryAxis" in bar and isinstance(bar["categoryAxis"], list), "no categoryAxis card")
    check(_is_solid(bar["categoryAxis"][0]["labelColor"]), "categoryAxis.labelColor not solid")
    check(bar["valueAxis"][0].get("gridlineStyle") == "dashed", "gridlineStyle not lowercased to 'dashed'")
    check(bar["valueAxis"][0].get("gridlineShow") is True, "gridlineShow not set true")
    check(bar["labels"][0].get("enableBackground") is True, "labels.enableBackground missing")
    check(bar["legend"][0].get("position") == "Bottom", "legend.position missing")
    check(bar["legend"][0].get("fontSize") == 60, "legend fontSize not clamped to 60")

    # 2) Visual-name mapping: Matrix -> pivotTable, Table -> tableEx.
    vs = build_visual_styles({
        "matrix": _style({"rowHeaderTextColor": "#111111", "showSubtotals": True}),
        "table": _style({"valuesTextColor": "#222222"}),
    })
    check("pivotTable" in vs and "matrix" not in vs, "matrix not mapped to pivotTable")
    check("tableEx" in vs and "table" not in vs, "table not mapped to tableEx")
    check("rowHeaders" in vs["pivotTable"]["*"], "matrix rowHeaders card missing")
    check("subTotals" in vs["pivotTable"]["*"], "matrix subTotals card missing")

    # 3) Scatter data labels -> categoryLabels (scatter has no `labels` card).
    vs = build_visual_styles({"scatterChart": _style({"dataLabelColor": "#333333"})})
    sc = vs["scatterChart"]["*"]
    check("categoryLabels" in sc and "labels" not in sc, "scatter labels not mapped to categoryLabels")

    # 4) Gauge -> axis / dataPoint / target / calloutValue.
    vs = build_visual_styles({"gauge": _style({
        "minValue": 0, "maxValue": 200, "fillColor": "#444444",
        "targetColor": "#555555", "showCallout": True, "calloutColor": "#666666",
    })})
    g = vs["gauge"]["*"]
    check(g["axis"][0].get("max") == 200, "gauge axis.max missing")
    check(_is_solid(g["dataPoint"][0]["fill"]), "gauge dataPoint.fill not solid")
    check(_is_solid(g["target"][0]["color"]), "gauge target.color not solid")

    # 5) Generic overrides pass through and merge with translated cards.
    theme = PowerBITheme()
    theme.visual_styles = {
        "barChart": {"*": {
            "formatting": {"legendPosition": "Top", "legendFontSize": 14},
            "title": [{"show": True, "fontColor": {"solid": {"color": "#123456"}}, "fontSize": 20}],
            "legend": [{"show": True, "position": "Right", "labelColor": {"solid": {"color": "#000000"}}}],
        }}
    }
    exported = theme.to_dict()["visualStyles"]["barChart"]["*"]
    check("title" in exported, "generic title card dropped")
    # generic legend (Right) should win over formatting legend (Top), and keep fontSize
    check(exported["legend"][0].get("position") == "Right", "generic legend did not win merge")
    check(exported["legend"][0].get("fontSize") == 14, "translated legend fontSize lost in merge")

    # 6b) Named style presets export alongside the default.
    vs = build_visual_styles({
        "columnChart": {
            "*": {"formatting": {"legendPosition": "Top"}},
            "Bold Blue": {"formatting": {"xAxisLabelColor": "#0000FF", "legendPosition": "Bottom"}},
        }
    })
    cc = vs["columnChart"]
    check("*" in cc and "Bold Blue" in cc, "named preset not exported alongside default")
    check("categoryAxis" in cc["Bold Blue"], "named preset formatting not translated")

    # 6) New theme-level colours export under their Power BI keys.
    theme = PowerBITheme()
    theme.second_level = "#AAAAAA"; theme.gradient_max = "#BBBBBB"
    td = theme.to_dict()
    check(td.get("secondLevelElements") == "#AAAAAA", "secondLevelElements not exported")
    check(td.get("maximum") == "#BBBBBB", "maximum gradient not exported")

    # 7) Round-trip: real cards import back into the formatter, and re-export is stable.
    original = {
        "barChart": {"*": {"formatting": {
            "xAxisLabelColor": "#FF0000", "gridlineStyle": "Dashed",
            "gridlineColor": "#00FF00", "legendPosition": "Bottom", "dataLabelFontSize": 12,
            "xAxisTitleText": "Quarter", "yAxisLogScale": True,
            "dataLabelDisplayUnits": "1000", "legendShowTitle": True, "legendTitleText": "Series",
        }}},
        "matrix": {"*": {"formatting": {
            "columnHeaderBackgroundColor": "#112233", "showSubtotals": True,
            "rowHeaderTextColor": "#445566",
        }}},
    }
    exported = build_visual_styles(original)          # -> real Power BI cards
    imported = import_visual_styles(exported)          # -> back to internal form
    bar_fmt = imported.get("barChart", {}).get("*", {}).get("formatting", {})
    check(bar_fmt.get("xAxisLabelColor") == "#FF0000", "round-trip lost xAxisLabelColor")
    check(bar_fmt.get("gridlineStyle") == "Dashed", "round-trip lost/garbled gridlineStyle")
    check(bar_fmt.get("legendPosition") == "Bottom", "round-trip lost legendPosition")
    check(bar_fmt.get("xAxisTitleText") == "Quarter", "round-trip lost axis title text")
    check(bar_fmt.get("yAxisLogScale") is True, "round-trip lost log scale")
    check(bar_fmt.get("dataLabelDisplayUnits") == "1000", "round-trip lost display units")
    check(bar_fmt.get("legendTitleText") == "Series", "round-trip lost legend title")
    # Matrix (pivotTable) maps back to the 'matrix' key with its formatting intact.
    check("matrix" in imported, "pivotTable did not map back to matrix on import")
    mat_fmt = imported.get("matrix", {}).get("*", {}).get("formatting", {})
    check(mat_fmt.get("showSubtotals") is True, "round-trip lost showSubtotals")
    check(mat_fmt.get("rowHeaderTextColor") == "#445566", "round-trip lost rowHeaderTextColor")

    # 8) Stage 5/6: state-keyed button hover, small multiples gating, generic containers.
    vs = build_visual_styles({"actionButton": _style({
        "buttonFillColor": "#111111", "buttonHoverFillColor": "#222222",
        "buttonTextColor": "#333333", "buttonHoverTextColor": "#444444",
    })})
    fill = vs["actionButton"]["*"]["fill"]
    check(isinstance(fill, list) and len(fill) == 2, "button hover fill not a 2-state array")
    check({e.get("$id") for e in fill} == {"default", "hover"}, "button fill states not default+hover")

    vs = build_visual_styles({
        "barChart": _style({"smColumnCount": 3, "smGridlineColor": "#ABCDEF"}),
        "waterfallChart": _style({"smColumnCount": 3}),
        "scatterChart": _style({"smColumnCount": 3}),
    })
    check("smallMultiplesLayout" in vs["barChart"]["*"], "barChart missing smallMultiplesLayout")
    check("smallMultiplesLayout" not in vs["waterfallChart"]["*"], "waterfall must not emit smallMultiplesLayout")
    check("smallMultiplesLayout" not in vs["scatterChart"]["*"], "scatter must not emit smallMultiplesLayout")

    # Generic Stage 6 container cards pass through export and re-import unchanged.
    from pbitheme.model import (
        build_divider_object, build_visual_tooltip_object,
        unpack_divider_object, unpack_visual_tooltip_object,
    )
    exported = build_visual_styles({"barChart": {"*": {
        "divider": build_divider_object(True, "#AABBCC", 2, "dashed"),
        "visualTooltip": build_visual_tooltip_object("#111111", "#222222", "#333333", 10),
    }}})
    imported = import_visual_styles(exported).get("barChart", {}).get("*", {})
    check(unpack_divider_object(imported) == (True, "#AABBCC", 2, "dashed"), "divider round-trip broken")
    check(unpack_visual_tooltip_object(imported)[0] == "#111111", "visualTooltip round-trip broken")

    # 9) Backlog: data bars (required props), blankRows matrix-only, stylePreset,
    #    plotArea, ratio line scatter-only, and their round-trip.
    vs = build_visual_styles({
        "tableEx": _style({"dataBarsShow": True, "dataBarsPositiveColor": "#00FF00",
                           "stylePreset": "Minimal", "defaultColumnWidth": 150,
                           "blankRowsShow": True}),
        "pivotTable": _style({"dataBarsShow": True, "blankRowsShow": True, "blankRowColor": "#EEEEEE"}),
        "scatterChart": _style({"ratioLineShow": True, "ratioLineColor": "#123456",
                               "plotAreaTransparency": 20}),
        "barChart": _style({"ratioLineShow": True, "plotAreaTransparency": 30}),
    })
    tdb = vs["tableEx"]["*"]["columnFormatting"][0]["dataBars"]
    check("reverseDirection" in tdb and "hideText" in tdb, "dataBars missing required reverseDirection/hideText")
    check("blankRows" not in vs["tableEx"]["*"], "tableEx must not emit blankRows (matrix-only)")
    check("blankRows" in vs["pivotTable"]["*"], "pivotTable should emit blankRows")
    check(vs["tableEx"]["*"]["stylePreset"][0].get("name") == "Minimal", "stylePreset.name missing")
    check("ratioLine" in vs["scatterChart"]["*"], "scatter should emit ratioLine")
    check("ratioLine" not in vs["barChart"]["*"], "bar must not emit ratioLine (scatter-only)")
    check(vs["barChart"]["*"]["plotArea"][0].get("transparency") == 30, "plotArea transparency missing")

    imported = import_visual_styles(vs)
    tex = imported.get("table", {}).get("*", {}).get("formatting", {})
    check(tex.get("dataBarsShow") is True, "data bars did not round-trip")
    check(tex.get("stylePreset") == "Minimal", "stylePreset did not round-trip")
    sca = imported.get("scatterChart", {}).get("*", {}).get("formatting", {})
    check(sca.get("ratioLineShow") is True, "ratio line did not round-trip")
    check(sca.get("plotAreaTransparency") == 20, "plotArea did not round-trip")

    # 10) Typography depth: bold / italic / font family + y-axis units/precision.
    vs = build_visual_styles({"barChart": _style({
        "xAxisBold": True, "xAxisItalic": True, "xAxisFontFamily": "Georgia",
        "yAxisBold": True, "yAxisDisplayUnits": "1000", "yAxisPrecision": 2,
        "legendItalic": True, "legendFontFamily": "Arial",
        "dataLabelBold": True, "dataLabelFontFamily": "Tahoma",
    })})
    b = vs["barChart"]["*"]
    check(b["categoryAxis"][0].get("bold") is True, "categoryAxis.bold missing")
    check(b["categoryAxis"][0].get("fontFamily") == "Georgia", "categoryAxis.fontFamily missing")
    check(b["valueAxis"][0].get("labelDisplayUnits") == 1000, "valueAxis.labelDisplayUnits missing")
    check(b["valueAxis"][0].get("labelPrecision") == 2, "valueAxis.labelPrecision missing")
    check(b["legend"][0].get("italic") is True, "legend.italic missing")
    check(b["labels"][0].get("bold") is True, "labels.bold missing")
    imp = import_visual_styles(vs)["barChart"]["*"]["formatting"]
    check(imp.get("xAxisBold") is True and imp.get("yAxisDisplayUnits") == "1000",
          "typography did not round-trip")

    print(f"Export invariants checked. Failures: {len(failures)}")
    if failures:
        for f in failures:
            print("  -", f)
        print("\n❌ Export translation is not producing valid Power BI cards.")
        return 1
    print("\n✅ Exported themes use valid Power BI cards and colours.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
