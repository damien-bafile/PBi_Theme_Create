#!/usr/bin/env python3
"""Regression test: every visual's every setting updates the live preview.

For each customizable visual type this opens the style dialog and, for every
formatting field and every generic-override section, changes the value and
asserts (a) it lands in the theme data and (b) it changes the rendered preview
SVG. Runs head-less via the off-screen Qt platform.

Run with::

    QT_QPA_PLATFORM=offscreen uv run python test_dynamic_preview.py
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QCheckBox, QComboBox, QSpinBox

from pbitheme.driver import AppDriver
from pbitheme.model import VISUAL_TYPES
from pbitheme.gui.widgets import ColorButton
from pbitheme.gui.visual_formatting_config import is_visual_customizable


def _instrument(dlg):
    """Capture the bytes the dialog renders into its preview SVG."""
    cap = {"bytes": None}
    svg = dlg._preview_svg
    original = svg.load

    def recording(data):
        try:
            cap["bytes"] = bytes(data)
        except Exception:  # pragma: no cover - defensive
            cap["bytes"] = None
        return original(data)

    svg.load = recording
    return cap


def _mutate(widget):
    """Change a formatter widget like a user would; return (new_value, restore)."""
    if isinstance(widget, ColorButton):
        old = widget.color()
        new = "#123456" if old.upper() != "#123456" else "#654321"
        widget.set_color(new)
        widget.colorChanged.emit(new)
        return new, lambda: (widget.set_color(old), widget.colorChanged.emit(old))
    if isinstance(widget, QCheckBox):
        old = widget.isChecked()
        widget.setChecked(not old)
        return widget.isChecked(), lambda: widget.setChecked(old)
    if isinstance(widget, QSpinBox):
        old = widget.value()
        new = widget.minimum() if old == widget.maximum() else widget.maximum()
        widget.setValue(new)
        return new, lambda: widget.setValue(old)
    if isinstance(widget, QComboBox):
        old = widget.currentIndex()
        widget.setCurrentIndex((old + 1) % widget.count())
        return widget.currentData(), lambda: widget.setCurrentIndex(old)
    return None, (lambda: None)


def main() -> int:
    driver = AppDriver()
    customizable = [(k, l) for k, l in VISUAL_TYPES if is_visual_customizable(k)]

    field_failures: list[str] = []
    generic_failures: list[str] = []
    n_fields = 0

    for key, label in customizable:
        dlg = driver.open_visual_dialog(key)
        panel = dlg._formatter_panel
        # Enable gridlines so gridline colour/thickness are visible (gated by style).
        if "gridlineStyle" in panel._field_widgets:
            panel.set_values({"gridlineStyle": "Solid"})
        cap = _instrument(dlg)

        # --- Formatting fields ---
        for field_key, widget in panel._field_widgets.items():
            dlg._update_preview()
            baseline = cap["bytes"]
            new_val, restore = _mutate(widget)
            after = cap["bytes"]
            n_fields += 1
            if panel.get_values().get(field_key) != new_val:
                field_failures.append(f"{key}.{field_key}: not captured in data")
            if baseline is None or after is None or baseline == after:
                field_failures.append(f"{key}.{field_key}: preview did not update")
            restore()

        # --- Generic overrides (test once per visual) ---
        dlg._update_preview()
        base = cap["bytes"]
        dlg._bg_check.setChecked(True)
        dlg._bg_color.set_color("#AB12CD")
        dlg._title_check.setChecked(True)
        dlg._title_color.set_color("#0A0B0C")
        dlg._legend_check.setChecked(True)
        dlg._legend_pos.setCurrentText("Bottom")
        after = cap["bytes"]
        if base is None or after is None or base == after:
            generic_failures.append(f"{key}: generic overrides did not update preview")
        # Ensure they persist to data too.
        dlg._on_ok()
        res = dlg.result_dict()
        for section in ("background", "title", "legend"):
            if section not in res:
                generic_failures.append(f"{key}: generic '{section}' not persisted")

    print(f"Customizable visuals tested: {len(customizable)}")
    print(f"Formatting fields tested:    {n_fields}")
    print(f"Field failures:              {len(field_failures)}")
    print(f"Generic-override failures:   {len(generic_failures)}")

    if field_failures or generic_failures:
        print("\nFAILURES:")
        for f in field_failures + generic_failures:
            print(f"  - {f}")
        print("\n❌ Some settings do not dynamically update the preview.")
        return 1

    print("\n✅ Every setting on every visual updates the live preview and persists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
