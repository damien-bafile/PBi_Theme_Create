"""Conformance tests: our output validates against the Power BI theme schema
and the visual-target list covers every visual the schema defines.
"""

import json
import os
import unittest

from jsonschema import Draft7Validator

from pbitheme.model import CARD_SCHEMA, VISUAL_TARGETS, PowerBITheme, VisualStyle
from pbitheme.validate import bundled_schema_path, validate_theme


def _full_feature_theme() -> PowerBITheme:
    theme = PowerBITheme("Full Feature")
    glob = theme.visual_styles[0]
    for card in CARD_SCHEMA:
        glob.enabled[card] = True
    for visual in VISUAL_TARGETS:
        if visual == "*":
            continue
        style = VisualStyle(visual)
        for card in CARD_SCHEMA:
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


if __name__ == "__main__":
    unittest.main()
