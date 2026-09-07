"""Screenshot capture for theme editor (CLI script + in-app action)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from PySide6.QtWidgets import QApplication, QWidget


DEFAULT_OUTPUT_PATH = Path("screenshots") / "theme_editor.png"


def capture_widget(widget: QWidget, output_path: str | Path) -> Path:
    """Render a widget to PNG via grab(). Used by both CLI and in-app menu."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not widget.grab().save(str(output_path), "PNG"):
        raise OSError(f"Failed to save screenshot to {output_path}")
    return output_path


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m pbitheme.screenshot",
        description="Render the theme editor off-screen and save a PNG (for AI-agent visual review).",
    )
    p.add_argument(
        "theme_json",
        nargs="?",
        default=None,
        help="Optional theme JSON to load first.",
    )
    p.add_argument(
        "output_png",
        nargs="?",
        default=None,
        help=f"Output PNG (default: {DEFAULT_OUTPUT_PATH}).",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Render the app and save a screenshot."""
    args = _build_arg_parser().parse_args(argv)

    # Must set QT_QPA_PLATFORM before QApplication
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from .model import PowerBITheme
    from .gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    theme = PowerBITheme.load(args.theme_json) if args.theme_json else None
    window = MainWindow(theme)
    window.resize(1000, 720)
    window.show()
    app.processEvents()

    out = Path(args.output_png) if args.output_png else DEFAULT_OUTPUT_PATH
    saved = capture_widget(window, out)
    print(f"Saved screenshot to {saved}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
