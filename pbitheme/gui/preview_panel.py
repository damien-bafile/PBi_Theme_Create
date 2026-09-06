"""Visual preview panel showing mockups of the current theme."""

from __future__ import annotations

from PySide6.QtCore import Qt
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

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(10)

        # Mockup labels and display
        mockup_info = [
            ("Bar Chart", "bar_chart", 0, 0),
            ("Table", "table", 0, 1),
            ("Line Chart", "line_chart", 1, 0),
            ("Card/KPI", "card_kpi", 1, 1),
        ]

        for label_text, key, row, col in mockup_info:
            # Label
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; margin-top: 8px;")
            grid.addWidget(label, row * 2, col)

            # SVG widget
            svg_widget = QSvgWidget()
            svg_widget.setMinimumSize(300, 200)
            svg_widget.setStyleSheet("border: 1px solid #ddd; border-radius: 4px;")
            self._svg_widgets[key] = svg_widget
            grid.addWidget(svg_widget, row * 2 + 1, col)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.addWidget(QWidget(), len(mockup_info) * 2, 0)  # Spacer at bottom

        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Initial update
        self.update_preview(self._theme)

    def update_preview(self, theme: PowerBITheme) -> None:
        """Update all mockups to reflect the current theme."""
        self._theme = theme
        mockups = generate_all_mockups(theme, size=300)

        for key, svg_widget in self._svg_widgets.items():
            svg_data = mockups.get(key, "")
            if svg_data:
                # Load SVG from string
                svg_widget.load(svg_data.encode("utf-8"))
