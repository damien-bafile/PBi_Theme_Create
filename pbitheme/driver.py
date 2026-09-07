"""Scriptable driver for the theme editor: control the app and take screenshots.

Unlike :mod:`pbitheme.screenshot` (which only renders the main window once),
this module lets you *drive* a live :class:`MainWindow` instance -- edit fields,
switch preview tabs, open the per-visual style dialog -- and capture a PNG of any
state along the way. It runs off-screen by default, so it works headlessly (CI,
AI-agent visual review) without a desktop session.

Example (headless gallery of a few states)::

    from pbitheme.driver import AppDriver

    d = AppDriver()                       # blank theme, off-screen
    d.set_name("Ocean")
    d.set_structural("foreground", "#0B3D66")
    d.set_data_colors(["#118DFF", "#12B5CB", "#E66C37"])
    d.snap("01_edited")                   # -> screenshots/01_edited.png
    d.select_preview_tab("JSON")
    d.snap("02_json")
    dlg = d.open_visual_dialog("barChart")
    d.snap_widget(dlg, "03_bar_dialog")
    d.close_dialog(dlg, accept=False)

Or from the shell::

    QT_QPA_PLATFORM=offscreen uv run python -m pbitheme.driver --demo
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

DEFAULT_SHOT_DIR = Path("screenshots")


class AppDriver:
    """Build a live :class:`MainWindow` and manipulate/screenshot it."""

    def __init__(
        self,
        theme_path: str | os.PathLike[str] | None = None,
        *,
        size: Tuple[int, int] = (1000, 720),
        on_screen: bool = False,
        shot_dir: str | os.PathLike[str] = DEFAULT_SHOT_DIR,
    ) -> None:
        # QT_QPA_PLATFORM must be set before QApplication is constructed. When a
        # QApplication already exists we can't change platforms, so we respect it.
        if not on_screen:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

        from PySide6.QtWidgets import QApplication, QTabWidget

        from .model import PowerBITheme
        from .gui.main_window import MainWindow

        self._QTabWidget = QTabWidget
        self.app = QApplication.instance() or QApplication([])

        theme = PowerBITheme.load(str(theme_path)) if theme_path else None
        self.window = MainWindow(theme)
        self.window.resize(*size)
        self.window.show()
        self.shot_dir = Path(shot_dir)
        self._pump()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _pump(self) -> None:
        """Flush pending events / repaints so a capture reflects the latest state."""
        self.app.processEvents()

    def _refresh(self) -> None:
        """Push widget state into the model + preview, then repaint."""
        # Some widget setters (e.g. ColorButton.set_color) don't emit their
        # ``changed`` signal, so we refresh the preview explicitly to stay safe.
        self.window._refresh_preview()
        self._pump()

    def _preview_tabs(self):
        tabs = self.window.findChild(self._QTabWidget)
        if tabs is None:  # pragma: no cover - defensive
            raise RuntimeError("Preview QTabWidget not found in MainWindow")
        return tabs

    # ------------------------------------------------------------------ #
    # Capture
    # ------------------------------------------------------------------ #
    def snap(self, name: str) -> Path:
        """Capture the whole main window to ``<shot_dir>/<name>.png``."""
        return self.snap_widget(self.window, name)

    def snap_widget(self, widget, name: str) -> Path:
        """Capture any widget (a dialog, a panel) to ``<shot_dir>/<name>.png``."""
        from .screenshot import capture_widget

        self._pump()
        out = self.shot_dir / (name if name.endswith(".png") else f"{name}.png")
        return capture_widget(widget, out)

    # ------------------------------------------------------------------ #
    # Controls -- editor fields
    # ------------------------------------------------------------------ #
    def set_name(self, text: str) -> "AppDriver":
        self.window._name_edit.setText(text)
        self._refresh()
        return self

    def set_structural(self, attr: str, hex_color: str) -> "AppDriver":
        """Set a structural colour by model attr (e.g. ``foreground``, ``background``)."""
        button = self.window._structural_buttons.get(attr)
        if button is None:
            valid = ", ".join(sorted(self.window._structural_buttons))
            raise KeyError(f"Unknown structural colour {attr!r}. Valid: {valid}")
        button.set_color(hex_color)
        self._refresh()
        return self

    def set_data_colors(self, colors: Sequence[str]) -> "AppDriver":
        self.window._data_editor.set_colors(list(colors))
        self._refresh()
        return self

    def set_text_class(
        self,
        name: str,
        *,
        font: str | None = None,
        size: int | None = None,
        color: str | None = None,
    ) -> "AppDriver":
        editor = self.window._text_editors.get(name)
        if editor is None:
            valid = ", ".join(sorted(self.window._text_editors))
            raise KeyError(f"Unknown text class {name!r}. Valid: {valid}")
        if font is not None:
            editor._font.setCurrentText(font)
        if size is not None:
            editor._size.setValue(size)
        if color is not None:
            editor._color.set_color(color)
        self._refresh()
        return self

    def select_preview_tab(self, which: int | str) -> "AppDriver":
        """Switch the right-hand preview between "Visual Preview" and "JSON Preview".

        Accepts a tab index, or a case-insensitive substring of the tab label
        (e.g. ``"json"`` or ``"visual"``).
        """
        tabs = self._preview_tabs()
        if isinstance(which, int):
            tabs.setCurrentIndex(which)
        else:
            target = which.lower()
            for i in range(tabs.count()):
                if target in tabs.tabText(i).lower():
                    tabs.setCurrentIndex(i)
                    break
            else:
                labels = [tabs.tabText(i) for i in range(tabs.count())]
                raise KeyError(f"No preview tab matching {which!r}. Have: {labels}")
        self._pump()
        return self

    # ------------------------------------------------------------------ #
    # Controls -- per-visual style dialog
    # ------------------------------------------------------------------ #
    def open_visual_dialog(self, visual_key: str):
        """Open (non-modally) the style dialog for ``visual_key`` and return it.

        The dialog is shown but not run modally, so you can ``snap_widget`` it and
        drive its widgets, then finish with :meth:`close_dialog`.
        """
        from .model import VISUAL_TYPES
        from .gui.visual_style_dialog import VisualStyleDialog

        label = dict(VISUAL_TYPES).get(visual_key, visual_key)
        existing = self.window._visual_styles.get(visual_key, {}).get("*", {})
        dialog = VisualStyleDialog(visual_key, label, existing, self.window, self.window._theme)
        dialog.show()
        self._pump()
        return dialog

    def close_dialog(self, dialog, *, accept: bool = False) -> "AppDriver":
        """Close a dialog opened with :meth:`open_visual_dialog`.

        When ``accept`` is true the dialog's result is merged into the theme
        (mirroring the app's own accept path); otherwise it's discarded.
        """
        if accept:
            result = dialog.result_dict()
            key = getattr(dialog, "_visual_key", None)
            if key is not None:
                if result:
                    self.window._visual_styles[key] = {"*": result}
                else:
                    self.window._visual_styles.pop(key, None)
            dialog.accept()
            self._refresh()
        else:
            dialog.reject()
            self._pump()
        return self

    # ------------------------------------------------------------------ #
    # Inspection / output
    # ------------------------------------------------------------------ #
    def to_json(self) -> str:
        """Return the current theme JSON (same text as the JSON preview tab)."""
        return self.window._collect_theme().to_json()

    def save_theme(self, path: str | os.PathLike[str]) -> Path:
        theme = self.window._collect_theme()
        theme.save(str(path))
        return Path(path)


# ---------------------------------------------------------------------- #
# Demo / CLI
# ---------------------------------------------------------------------- #
def _run_demo(shot_dir: Path, theme_path: Optional[str]) -> List[Path]:
    """Produce a small gallery demonstrating control + capture."""
    d = AppDriver(theme_path, shot_dir=shot_dir)
    shots: List[Path] = []

    shots.append(d.snap("driver_01_initial"))

    d.set_name("Ocean Demo")
    d.set_structural("foreground", "#0B3D66")
    d.set_data_colors(["#118DFF", "#12B5CB", "#E66C37", "#6B007B"])
    shots.append(d.snap("driver_02_edited_visual_preview"))

    d.select_preview_tab("JSON")
    shots.append(d.snap("driver_03_json_preview"))
    d.select_preview_tab("Visual")

    dlg = d.open_visual_dialog("barChart")
    shots.append(d.snap_widget(dlg, "driver_04_bar_style_dialog"))
    d.close_dialog(dlg, accept=False)

    return shots


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pbitheme.driver",
        description="Drive the theme editor and capture screenshots (headless-friendly).",
    )
    parser.add_argument("--theme", default=None, help="Theme JSON to load first.")
    parser.add_argument(
        "--shot-dir", default=str(DEFAULT_SHOT_DIR), help="Directory for PNG output."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a scripted demo that exercises editing, tab switching and a dialog.",
    )
    args = parser.parse_args(argv)

    if not args.demo:
        parser.error("Nothing to do. Pass --demo, or import AppDriver from your own script.")

    shots = _run_demo(Path(args.shot_dir), args.theme)
    for path in shots:
        print(f"Saved {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
