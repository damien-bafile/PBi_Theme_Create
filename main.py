#!/usr/bin/env python3
"""Entry point for the Power BI Theme Creator GUI.

Run with::

    python main.py

The application logic lives in :func:`pbitheme.gui.main` so that the installed
``pbitheme`` console command and ``python -m pbitheme`` share the same launcher.
"""

from __future__ import annotations

from pbitheme.gui import main

if __name__ == "__main__":
    raise SystemExit(main())
