"""Conformance tests: our output validates against the Power BI theme schema
and the visual-target list covers every visual the schema defines.
"""

import json
import os
import unittest

from jsonschema import Draft7Validator

from pbitheme.model import (
    VISUAL_CARD_SCHEMA,
    VISUAL_TARGETS,
    PowerBITheme,
    VisualStyle,
    cards_for,
)
from pbitheme.validate import bundled_schema_path, validate_theme


def _full_feature_theme() -> PowerBITheme:
    """A theme enabling every card of every visual's own schema."""
    theme = PowerBITheme("Full Feature")
    glob = theme.visual_styles[0]
    for card in glob.schema:
        glob.enabled[card] = True
    for visual in VISUAL_TARGETS:
        if visual == "*":
            continue
        style = VisualStyle(visual)
        for card in style.schema:
            style.enabled[card] = True
        theme.visual_styles.append(style)
    return theme


class ConformanceTests(unittest.TestCase):
    def setUp(self):
        with open(bundled_schema_path(), encoding="utf-8") as fh:
            self.schema = json.load(fh)

    def test_default_theme_is_valid(self):
        self.assertEqual(validate_theme(PowerBITheme("Default").to_dict()), [])

    def test_full_feature_theme_is_valid(self):
        self.assertEqual(validate_theme(_full_feature_theme().to_dict()), [])

    def test_visual_targets_cover_all_schema_visuals(self):
        schema_visuals = set(self.schema["properties"]["visualStyles"]["properties"])
        ours = set(VISUAL_TARGETS) - {"*"}
        self.assertEqual(ours - schema_visuals, set(), "invalid visual names")
        self.assertEqual(schema_visuals - ours, set(), "missing visual names")

    def test_round_trip_is_stable(self):
        original = _full_feature_theme().to_dict()
        reloaded = PowerBITheme.from_dict(json.loads(json.dumps(original))).to_dict()
        self.assertEqual(reloaded, original)

    def test_label_display_units_is_integer(self):
        theme = PowerBITheme("X")
        theme.visual_styles[0].enabled["labels"] = True
        labels = theme.to_dict()["visualStyles"]["*"]["*"]["labels"][0]
        self.assertIsInstance(labels["labelDisplayUnits"], int)

    def test_detailed_visuals_have_dedicated_cards(self):
        # Matrix, Table and Slicer expose more than the generic card set.
        expected = {
            "pivotTable": {"grid", "columnHeaders", "rowHeaders", "subTotals"},
            "tableEx": {"grid", "columnHeaders", "values", "stylePreset"},
            "slicer": {"general", "header", "items", "selection", "slider"},
        }
        for visual, cards in expected.items():
            self.assertTrue(cards.issubset(set(cards_for(visual))), visual)

    def test_matrix_detailed_theme_validates(self):
        theme = PowerBITheme("Matrix")
        style = VisualStyle("pivotTable")
        for card in style.schema:
            style.enabled[card] = True
        theme.visual_styles = [style]
        self.assertEqual(validate_theme(theme.to_dict()), [])

    def test_unmodelled_content_is_preserved(self):
        external = {
            "$schema": "https://example/schema.json",
            "name": "External",
            "dataColors": ["#010203"],
            "firstLevelElements": "#111111",
            "maximum": "#00FF00",
            "textClasses": {
                "title": {"fontFace": "Arial", "fontSize": 14, "color": "#000000",
                          "bold": True},
                "customClass": {"fontSize": 9},
            },
            "visualStyles": {
                "pivotTable": {
                    "*": {
                        "grid": [{"gridHorizontal": True, "someFutureProp": 42}],
                        "unknownCard": [{"foo": "bar"}],
                    },
                    "MyPreset": {"columnHeaders": [{"fontSize": 20}]},
                },
                "customVisualGuid": {"*": {"weird": [{"x": 1}]}},
            },
        }
        out = PowerBITheme.from_dict(json.loads(json.dumps(external))).to_dict()
        self.assertEqual(out["$schema"], external["$schema"])
        self.assertEqual(out["firstLevelElements"], "#111111")
        self.assertEqual(out["maximum"], "#00FF00")
        self.assertTrue(out["textClasses"]["title"]["bold"])
        self.assertEqual(out["textClasses"]["customClass"], {"fontSize": 9})
        pv = out["visualStyles"]["pivotTable"]
        self.assertEqual(pv["*"]["grid"][0]["someFutureProp"], 42)
        self.assertEqual(pv["*"]["unknownCard"], [{"foo": "bar"}])
        self.assertEqual(pv["MyPreset"], {"columnHeaders": [{"fontSize": 20}]})
        self.assertEqual(out["visualStyles"]["customVisualGuid"],
                         {"*": {"weird": [{"x": 1}]}})

    def test_modelled_text_class_keeps_original_fields(self):
        # A partial class stays partial; editing a field adds just that field.
        theme = PowerBITheme.from_dict(
            {"name": "P", "textClasses": {"title": {"fontSize": 9}}}
        )
        title = theme.text_classes["title"]
        self.assertEqual(title.to_dict(), {"fontSize": 9})
        title.color = "#ABCDEF"
        title.present.add("color")
        self.assertEqual(sorted(title.to_dict()), ["color", "fontSize"])
        # A brand-new theme fully specifies its text classes.
        self.assertEqual(
            sorted(PowerBITheme("New").text_classes["title"].to_dict()),
            ["color", "fontFace", "fontSize"],
        )

    def test_charts_have_dedicated_cards(self):
        cartesian = set(cards_for("columnChart"))
        self.assertTrue(
            {"legend", "categoryAxis", "valueAxis", "dataPoint", "labels"}.issubset(
                cartesian
            )
        )
        circular = set(cards_for("pieChart"))
        self.assertTrue({"legend", "dataPoint", "labels"}.issubset(circular))
        self.assertNotIn("categoryAxis", circular)  # circular charts have no axes

    def test_chart_detailed_theme_validates(self):
        for visual in ("columnChart", "lineChart", "scatterChart", "pieChart"):
            style = VisualStyle(visual)
            for card in style.schema:
                style.enabled[card] = True
            theme = PowerBITheme(visual)
            theme.visual_styles = [style]
            self.assertEqual(validate_theme(theme.to_dict()), [], visual)

    def test_more_visuals_have_dedicated_cards(self):
        expected = {
            "multiRowCard": {"dataLabels", "cardTitle", "card"},
            "kpi": {"indicator", "trendline", "goals"},
            "gauge": {"dataPoint", "calloutValue"},
            "map": {"legend", "dataPoint"},
            "filledMap": {"legend", "dataPoint"},
        }
        for visual, cards in expected.items():
            self.assertTrue(cards.issubset(set(cards_for(visual))), visual)

    def test_every_dedicated_visual_validates(self):
        # Enabling every card of every visual's own schema is schema-valid.
        for visual in VISUAL_CARD_SCHEMA:
            style = VisualStyle(visual)
            for card in style.schema:
                style.enabled[card] = True
            theme = PowerBITheme(visual)
            theme.visual_styles = [style]
            self.assertEqual(validate_theme(theme.to_dict()), [], visual)

    def test_slicer_orientation_is_integer(self):
        style = VisualStyle("slicer")
        style.enabled["general"] = True
        theme = PowerBITheme("S")
        theme.visual_styles = [style]
        general = theme.to_dict()["visualStyles"]["slicer"]["*"]["general"][0]
        self.assertIsInstance(general["orientation"], int)


if __name__ == "__main__":
    unittest.main()
