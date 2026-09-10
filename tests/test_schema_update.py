"""Offline tests for the schema-update checker (no real network)."""

from __future__ import annotations

import json
import unittest

from pbitheme import schema_update as su


def _payload(*names: str) -> bytes:
    return json.dumps([{"name": n} for n in names]).encode()


class SchemaUpdateTests(unittest.TestCase):
    def test_version_tuple(self):
        self.assertEqual(su._version_tuple("reportThemeSchema-2.157.json"), (2, 157))
        self.assertEqual(su._version_tuple("2.161"), (2, 161))
        self.assertEqual(su._version_tuple("2.99"), (2, 99))
        self.assertTrue(su._version_tuple("2.161") > su._version_tuple("2.157"))
        # Malformed inputs fall back to (0,) so comparisons never explode.
        self.assertEqual(su._version_tuple("garbage"), (0,))
        self.assertEqual(su._version_tuple("reportThemeSchema-.json"), (0,))

    def test_parse_latest(self):
        payload = _payload(
            "reportThemeSchema-2.156.json",
            "reportThemeSchema-2.161.json",
            "reportThemeSchema-2.99.json",
            "README.md",
        )
        self.assertEqual(su.parse_latest(payload), "2.161")
        self.assertIsNone(su.parse_latest(_payload("README.md")))
        self.assertIsNone(su.parse_latest(b"[]"))
        self.assertIsNone(su.parse_latest(b"not json"))
        self.assertIsNone(su.parse_latest(b"{}"))  # object, not a list

    def test_check_for_update_available(self):
        orig = su._http_get
        su._http_get = lambda url, timeout=10: _payload("reportThemeSchema-2.161.json")
        try:
            info = su.check_for_update(bundled="2.157")
        finally:
            su._http_get = orig
        self.assertEqual(info["latest"], "2.161")
        self.assertTrue(info["update_available"])
        self.assertIsNone(info["error"])

    def test_check_for_update_current(self):
        orig = su._http_get
        su._http_get = lambda url, timeout=10: _payload("reportThemeSchema-2.157.json")
        try:
            info = su.check_for_update(bundled="2.157")
        finally:
            su._http_get = orig
        self.assertFalse(info["update_available"])
        self.assertIsNone(info["error"])

    def test_check_for_update_network_error(self):
        orig = su._http_get

        def boom(url, timeout=10):
            raise OSError("no network")

        su._http_get = boom
        try:
            info = su.check_for_update(bundled="2.157")
        finally:
            su._http_get = orig
        self.assertIsNone(info["latest"])
        self.assertFalse(info["update_available"])
        self.assertIn("no network", info["error"])

    def test_check_for_update_defaults_to_bundled(self):
        # With no explicit `bundled`, it reads the packaged schema version.
        from pbitheme.validate import schema_version

        orig = su._http_get
        su._http_get = lambda url, timeout=10: _payload("reportThemeSchema-2.157.json")
        try:
            info = su.check_for_update()
        finally:
            su._http_get = orig
        self.assertEqual(info["bundled"], schema_version())


if __name__ == "__main__":
    unittest.main()
