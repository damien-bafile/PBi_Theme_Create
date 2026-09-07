#!/usr/bin/env python3
"""Entry point for the Power BI Theme Creator GUI.

Run with::

    python main.py
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    # Suppress platform warnings (e.g., mouse grab warnings on Wayland)
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "")
    os.environ.setdefault("QT_DEBUG_PLUGINS", "0")

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        sys.stderr.write(
            "PySide6 is required to run the GUI.\n"
            "Install dependencies with:  uv sync\n"
        )
        return 1

    from pbitheme.gui import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Power BI Theme Creator")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
