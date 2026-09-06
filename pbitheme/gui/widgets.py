"""Reusable Qt widgets used by the theme editor.

Each widget is a self-contained class that exposes a ``changed`` signal so the
main window can rebuild the live JSON preview whenever anything is edited.
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFontComboBox,
    QGridLayout,
    QScrollArea,
)

from ..model import PowerBITheme, TextClass, VISUAL_TYPES, is_valid_hex, normalise_hex


class ColorButton(QPushButton):
    """A button that shows a colour swatch and opens a colour picker."""

    colorChanged = Signal(str)

    def __init__(self, color: str = "#FFFFFF", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = normalise_hex(color) if is_valid_hex(color) else "#FFFFFF"
        self.setFixedSize(120, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._choose_color)
        self._refresh()

    def color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        if is_valid_hex(color):
            self._color = normalise_hex(color)
            self._refresh()

    def _choose_color(self) -> None:
        chosen = QColorDialog.getColor(QColor(self._color), self, "Pick a colour")
        if chosen.isValid():
            self._color = chosen.name().upper()
            self._refresh()
            self.colorChanged.emit(self._color)

    def _refresh(self) -> None:
        # Choose readable text colour based on luminance.
        c = QColor(self._color)
        luminance = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
        text = "#000000" if luminance > 140 else "#FFFFFF"
        self.setText(self._color)
        self.setStyleSheet(
            f"background-color: {self._color}; color: {text};"
            "border: 1px solid #888; border-radius: 4px; font-family: monospace;"
        )


class DataColorsEditor(QWidget):
    """Editable list of data colours with add / remove controls."""

    changed = Signal()

    def __init__(self, colors: List[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: List[ColorButton] = []

        self._rows = QVBoxLayout()
        self._rows.setContentsMargins(0, 0, 0, 0)

        controls = QHBoxLayout()
        add_btn = QPushButton("+ Add colour")
        add_btn.clicked.connect(lambda: self._add_color("#118DFF", emit=True))
        remove_btn = QPushButton("- Remove last")
        remove_btn.clicked.connect(self._remove_last)
        controls.addWidget(add_btn)
        controls.addWidget(remove_btn)
        controls.addStretch(1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self._rows)
        outer.addLayout(controls)

        self.set_colors(colors)

    def colors(self) -> List[str]:
        return [btn.color() for btn in self._buttons]

    def set_colors(self, colors: List[str]) -> None:
        while self._buttons:
            self._remove_last(emit=False)
        for color in colors:
            self._add_color(color, emit=False)
        self.changed.emit()

    def _add_color(self, color: str, emit: bool) -> None:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        index = len(self._buttons) + 1
        layout.addWidget(QLabel(f"{index}."))
        button = ColorButton(color)
        button.colorChanged.connect(lambda _c: self.changed.emit())
        layout.addWidget(button)
        layout.addStretch(1)

        self._buttons.append(button)
        self._rows.addWidget(row)
        if emit:
            self.changed.emit()

    def _remove_last(self, emit: bool = True) -> None:
        if not self._buttons:
            return
        self._buttons.pop()
        item = self._rows.takeAt(self._rows.count() - 1)
        if item and item.widget():
            item.widget().deleteLater()
        if emit:
            self.changed.emit()


class TextClassEditor(QWidget):
    """Font face, size and colour editor for a single text class."""

    changed = Signal()

    def __init__(self, text_class: TextClass, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name = text_class.name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._font = QFontComboBox()
        self._font.setCurrentText(text_class.font_face)
        self._font.currentFontChanged.connect(lambda _f: self.changed.emit())

        self._size = QSpinBox()
        self._size.setRange(4, 120)
        self._size.setValue(text_class.font_size)
        self._size.setSuffix(" pt")
        self._size.valueChanged.connect(lambda _v: self.changed.emit())

        self._color = ColorButton(text_class.color)
        self._color.colorChanged.connect(lambda _c: self.changed.emit())

        layout.addWidget(self._font, 2)
        layout.addWidget(self._size)
        layout.addWidget(self._color)

    def value(self) -> TextClass:
        return TextClass(
            name=self._name,
            font_face=self._font.currentFont().family(),
            font_size=self._size.value(),
            color=self._color.color(),
        )


class VisualStylesChecklist(QWidget):
    """Scrollable checklist of Power BI visual types with customization status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status_labels: dict[str, QLabel] = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)

        for row, (key, label) in enumerate(VISUAL_TYPES):
            name_label = QLabel(label)
            status_label = QLabel("✗")
            status_label.setStyleSheet("color: #D64550; font-weight: bold; min-width: 30px;")
            grid.addWidget(name_label, row, 0)
            grid.addWidget(status_label, row, 1)
            self._status_labels[key] = status_label

        # Add a stretch row at the end to push all items to the top
        grid.addWidget(QWidget(), len(VISUAL_TYPES), 0)
        grid.setRowStretch(len(VISUAL_TYPES), 1)

        scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def set_theme(self, theme: PowerBITheme) -> None:
        """Update the checklist based on which visuals are customised."""
        for key, label in self._status_labels.items():
            if theme.is_visual_customised(key):
                label.setText("✓")
                label.setStyleSheet("color: #1AAB40; font-weight: bold; min-width: 30px;")
            else:
                label.setText("✗")
                label.setStyleSheet("color: #D64550; font-weight: bold; min-width: 30px;")
