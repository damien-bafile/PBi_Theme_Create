"""Visual preview panel showing mockups of the current theme."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtSvgWidgets import QSvgWidget

from ..model import PowerBITheme
from .preview_mockups import generate_all_mockups
from .theme import BORDER_HAIRLINE


#: Viewport width (px) at/above which the mockups lay out in two columns.
TWO_COLUMN_MIN_WIDTH = 500


class PreviewPanel(QWidget):
    """Display visual mockups of Power BI visuals using the current theme."""

    def __init__(self, theme: PowerBITheme | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme or PowerBITheme()
        self._svg_widgets: dict[str, QSvgWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for mockups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll = scroll

        container = QWidget()
        self._grid = QGridLayout(container)
        self._grid.setSpacing(10)

        # (label, key) in display order; laid out into 1 or 2 columns responsively.
        self._mockups = [
            ("Bar Chart", "bar_chart"),
            ("Table", "table"),
            ("Line Chart", "line_chart"),
            ("Card/KPI", "card_kpi"),
        ]
        self._labels: dict[str, QLabel] = {}
        for label_text, key in self._mockups:
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; margin-top: 8px;")
            self._labels[key] = label
            svg_widget = QSvgWidget()
            # Small minimum so a single narrow column never triggers horizontal scroll;
            # the SVG scales up to fill whatever width the pane offers.
            svg_widget.setMinimumSize(220, 150)
            svg_widget.setStyleSheet(f"border: 1px solid {BORDER_HAIRLINE}; border-radius: 4px;")
            self._svg_widgets[key] = svg_widget

        self._columns = 0  # force first layout
        self._populate_grid(2)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Initial update
        self.update_preview(self._theme)

    def _populate_grid(self, columns: int) -> None:
        """(Re)lay the mockups into *columns* columns (1 when the pane is narrow)."""
        if columns == self._columns:
            return
        self._columns = columns
        while self._grid.count():
            self._grid.takeAt(0)
        for i, (_label, key) in enumerate(self._mockups):
            row, col = divmod(i, columns)
            self._grid.addWidget(self._labels[key], row * 2, col)
            self._grid.addWidget(self._svg_widgets[key], row * 2 + 1, col)
        for c in range(2):
            self._grid.setColumnStretch(c, 1 if c < columns else 0)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        # Two columns need room for two ~220px tiles + spacing; below that, stack.
        want = 2 if self._scroll.viewport().width() >= TWO_COLUMN_MIN_WIDTH else 1
        self._populate_grid(want)

    def update_preview(self, theme: PowerBITheme, visual_styles: Dict[str, Any] | None = None) -> None:
        """Update all mockups to reflect the current theme and visual styles."""
        self._theme = theme
        visual_styles = visual_styles or {}
        mockups = generate_all_mockups(theme, visual_styles=visual_styles, size=300)

        for key, svg_widget in self._svg_widgets.items():
            svg_data = mockups.get(key, "")
            if svg_data:
                # Load SVG from string using QByteArray
                svg_bytes = QByteArray(svg_data.encode("utf-8"))
                svg_widget.load(svg_bytes)
