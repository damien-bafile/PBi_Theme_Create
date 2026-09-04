#!/usr/bin/env python3
"""Entry point for the Power BI Theme Creator GUI.

Run with::

    python main.py
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        sys.stderr.write(
            "PySide6 is required to run the GUI.\n"
            "Install it with:  pip install -r requirements.txt\n"
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
