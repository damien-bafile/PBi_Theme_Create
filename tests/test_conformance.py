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


if __name__ == "__main__":
    unittest.main()
