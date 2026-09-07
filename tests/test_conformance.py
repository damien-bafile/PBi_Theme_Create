"""Conformance tests.

Validate that the themes this app exports conform to the official Power BI
report theme JSON schema (bundled from microsoft/powerbi-desktop-samples).
This exercises the real export pipeline (``PowerBITheme.to_dict`` ->
``theme_export.build_visual_styles``) against Microsoft's schema.
"""

import json
import os
import unittest

from pbitheme.model import PowerBITheme
from pbitheme.validate import bundled_schema_path, schema_version, validate_theme

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_DEMO = os.path.join(_REPO_ROOT, "demo_visual_styles.json")

# A representative chart formatting block (keys taken from the export tests).
_BAR_FORMATTING = {
    "xAxisLabelColor": "#FF0000",
    "xAxisLabelFontSize": 12,
    "yAxisTitleColor": "#00FF00",
    "gridlineStyle": "Dashed",
    "gridlineColor": "#123456",
    "gridlineThickness": 2,
    "dataLabelColor": "#0000FF",
    "dataLabelBackground": True,
    "legendPosition": "Bottom",
    "legendTextColor": "#ABCDEF",
    "legendFontSize": 12,
}


class ConformanceTests(unittest.TestCase):
    def test_bundled_schema_present(self):
        self.assertIsNotNone(bundled_schema_path(), "bundled schema missing")
        self.assertIsNotNone(schema_version())

    def test_default_theme_is_valid(self):
        self.assertEqual(validate_theme(PowerBITheme("Default").to_dict()), [])

    def test_demo_theme_is_valid(self):
        with open(_DEMO, encoding="utf-8") as fh:
            demo = json.load(fh)
        self.assertEqual(validate_theme(demo), [])

    def test_populated_export_is_valid(self):
        theme = PowerBITheme("Populated")
        theme.visual_styles = {"barChart": {"*": {"formatting": dict(_BAR_FORMATTING)}}}
        errors = validate_theme(theme.to_dict())
        self.assertEqual(errors, [], errors[:5])

    def test_export_round_trip_stays_valid(self):
        theme = PowerBITheme("RoundTrip")
        theme.visual_styles = {"barChart": {"*": {"formatting": dict(_BAR_FORMATTING)}}}
        exported = theme.to_dict()
        reimported = PowerBITheme.from_dict(json.loads(json.dumps(exported)))
        self.assertEqual(validate_theme(reimported.to_dict()), [])

    def test_page_and_report_are_valid(self):
        from pbitheme.gui.visual_formatting_config import get_formatting_sections

        def _sample(f):
            return {"color": "#3A6EA5", "boolean": True,
                    "number": int(((f.min_val or 0) + (f.max_val or 10)) // 2) or (f.min_val or 0),
                    "dropdown": (f.options[0][0] if f.options else ""),
                    "text": "x"}.get(f.field_type)

        for visual, cards in (("page", {"outspace", "outspacePane", "filterCard"}),
                              ("report", {"outspacePane", "filterCard"})):
            secs = get_formatting_sections(visual)
            self.assertTrue(secs, visual)
            fmt = {f.key: _sample(f) for s in secs for f in s.fields}
            theme = PowerBITheme("pr")
            theme.visual_styles = {visual: {"*": {"formatting": fmt}}}
            out = theme.to_dict()
            self.assertEqual(validate_theme(out), [], visual)
            self.assertTrue(cards.issubset(set(out["visualStyles"][visual]["*"])), visual)
            # round-trips: import then re-export is stable
            reimported = PowerBITheme.from_dict(json.loads(json.dumps(out)))
            self.assertEqual(reimported.to_dict()["visualStyles"], out["visualStyles"], visual)

    def test_newer_visuals_are_valid(self):
        from pbitheme.gui.visual_formatting_config import get_formatting_sections

        def _sample(f):
            return {"color": "#3A6EA5", "boolean": True,
                    "number": int(((f.min_val or 0) + (f.max_val or 10)) // 2) or (f.min_val or 0),
                    "dropdown": (f.options[0][0] if f.options else ""),
                    "text": "x"}.get(f.field_type)

        for visual in ("cardVisual", "advancedSlicerVisual", "listSlicer",
                       "textSlicer", "pageNavigator", "bookmarkNavigator"):
            secs = get_formatting_sections(visual)
            self.assertTrue(secs, visual)
            fmt = {f.key: _sample(f) for s in secs for f in s.fields}
            theme = PowerBITheme("nv")
            theme.visual_styles = {visual: {"*": {"formatting": fmt}}}
            out = theme.to_dict()
            self.assertEqual(validate_theme(out), [], visual)
            reimported = PowerBITheme.from_dict(json.loads(json.dumps(out)))
            self.assertEqual(reimported.to_dict()["visualStyles"], out["visualStyles"], visual)


if __name__ == "__main__":
    unittest.main()
