"""Qt GUI package for the Power BI theme creator."""

from __future__ import annotations

import os
import sys

from .main_window import MainWindow

__all__ = ["MainWindow", "main"]


def main() -> int:
    """Launch the Power BI Theme Creator GUI (console entry point)."""
    # Suppress platform warnings (e.g. mouse grab warnings on Wayland).
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "")
    os.environ.setdefault("QT_DEBUG_PLUGINS", "0")

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        sys.stderr.write(
            "PySide6 is required to run the GUI.\n"
            "Install it with:  pip install -e .  (or: pip install pbitheme)\n"
        )
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("Power BI Theme Creator")
    app.setOrganizationName("PBiThemeCreator")
    from . import theme
    theme.apply_light_palette(app)  # own the canvas so DESIGN.md is real everywhere
    window = MainWindow()
    window.show()
    return app.exec()
