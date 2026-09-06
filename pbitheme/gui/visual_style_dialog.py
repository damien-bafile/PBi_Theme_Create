"""Modal dialog for editing per-visual style overrides."""

from __future__ import annotations

import json
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QPlainTextEdit,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
)

from ..model import (
    LEGEND_POSITIONS,
    build_background_object,
    build_border_object,
    build_title_object,
    build_data_labels_object,
    build_legend_object,
    unpack_background_object,
    unpack_border_object,
    unpack_title_object,
    unpack_data_labels_object,
    unpack_legend_object,
    merge_visual_style_entry,
)
from .widgets import ColorButton


class VisualStyleDialog(QDialog):
    """Edit structured and raw-JSON overrides for a single visual type's style."""

    def __init__(
        self,
        visual_key: str,
        visual_label: str,
        existing_obj: Dict[str, Any],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Edit {visual_label} Style")
        self.resize(600, 700)
        self._visual_key = visual_key
        self._result: Dict[str, Any] | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Style overrides: {visual_label}"))

        # ---- Background section ---- #
        bg_box = QGroupBox("Background")
        bg_layout = QFormLayout(bg_box)
        self._bg_check = QCheckBox("Override")
        self._bg_color = ColorButton("#FFFFFF")
        self._bg_alpha = QSpinBox()
        self._bg_alpha.setRange(0, 100)
        self._bg_alpha.setSuffix("%")
        bg_show, bg_color, bg_trans = unpack_background_object(existing_obj)
        self._bg_color.set_color(bg_color)
        self._bg_alpha.setValue(bg_trans)
        bg_layout.addRow(self._bg_check, QLabel())
        bg_layout.addRow("Color", self._bg_color)
        bg_layout.addRow("Transparency", self._bg_alpha)
        self._bg_check.toggled.connect(lambda c: self._bg_color.setEnabled(c))
        self._bg_check.toggled.connect(lambda c: self._bg_alpha.setEnabled(c))
        self._bg_color.setEnabled(False)
        self._bg_alpha.setEnabled(False)
        layout.addWidget(bg_box)

        # ---- Border section ---- #
        border_box = QGroupBox("Border")
        border_layout = QFormLayout(border_box)
        self._border_check = QCheckBox("Override")
        self._border_color = ColorButton("#000000")
        border_show, border_color = unpack_border_object(existing_obj)
        self._border_color.set_color(border_color)
        border_layout.addRow(self._border_check, QLabel())
        border_layout.addRow("Color", self._border_color)
        self._border_check.toggled.connect(lambda c: self._border_color.setEnabled(c))
        self._border_color.setEnabled(False)
        layout.addWidget(border_box)

        # ---- Title section ---- #
        title_box = QGroupBox("Title")
        title_layout = QFormLayout(title_box)
        self._title_check = QCheckBox("Override")
        self._title_font = ColorButton.__bases__[0].__subclasses__()[0]()  # Get QFontComboBox
        # Simpler approach: just create it fresh
        from PySide6.QtWidgets import QFontComboBox
        self._title_font = QFontComboBox()
        self._title_size = QSpinBox()
        self._title_size.setRange(4, 120)
        self._title_size.setSuffix(" pt")
        self._title_color = ColorButton("#252423")
        title_show, title_font, title_size, title_color = unpack_title_object(existing_obj)
        self._title_font.setCurrentText(title_font)
        self._title_size.setValue(title_size)
        self._title_color.set_color(title_color)
        title_layout.addRow(self._title_check, QLabel())
        title_layout.addRow("Font", self._title_font)
        title_layout.addRow("Size", self._title_size)
        title_layout.addRow("Color", self._title_color)
        self._title_check.toggled.connect(lambda c: self._title_font.setEnabled(c))
        self._title_check.toggled.connect(lambda c: self._title_size.setEnabled(c))
        self._title_check.toggled.connect(lambda c: self._title_color.setEnabled(c))
        self._title_font.setEnabled(False)
        self._title_size.setEnabled(False)
        self._title_color.setEnabled(False)
        layout.addWidget(title_box)

        # ---- Data labels section ---- #
        labels_box = QGroupBox("Data Labels")
        labels_layout = QFormLayout(labels_box)
        self._labels_check = QCheckBox("Override")
        self._labels_color = ColorButton("#252423")
        self._labels_size = QSpinBox()
        self._labels_size.setRange(4, 120)
        self._labels_size.setSuffix(" pt")
        labels_show, labels_color, labels_size = unpack_data_labels_object(existing_obj)
        self._labels_color.set_color(labels_color)
        self._labels_size.setValue(labels_size)
        labels_layout.addRow(self._labels_check, QLabel())
        labels_layout.addRow("Color", self._labels_color)
        labels_layout.addRow("Font Size", self._labels_size)
        self._labels_check.toggled.connect(lambda c: self._labels_color.setEnabled(c))
        self._labels_check.toggled.connect(lambda c: self._labels_size.setEnabled(c))
        self._labels_color.setEnabled(False)
        self._labels_size.setEnabled(False)
        layout.addWidget(labels_box)

        # ---- Legend section ---- #
        legend_box = QGroupBox("Legend")
        legend_layout = QFormLayout(legend_box)
        self._legend_check = QCheckBox("Override")
        self._legend_pos = QComboBox()
        self._legend_pos.addItems(LEGEND_POSITIONS)
        self._legend_color = ColorButton("#252423")
        legend_show, legend_pos, legend_color = unpack_legend_object(existing_obj)
        self._legend_pos.setCurrentText(legend_pos)
        self._legend_color.set_color(legend_color)
        legend_layout.addRow(self._legend_check, QLabel())
        legend_layout.addRow("Position", self._legend_pos)
        legend_layout.addRow("Color", self._legend_color)
        self._legend_check.toggled.connect(lambda c: self._legend_pos.setEnabled(c))
        self._legend_check.toggled.connect(lambda c: self._legend_color.setEnabled(c))
        self._legend_pos.setEnabled(False)
        self._legend_color.setEnabled(False)
        layout.addWidget(legend_box)

        # ---- Advanced JSON section ---- #
        layout.addWidget(QLabel("Advanced JSON (raw styleName '*' object)"))
        self._advanced_edit = QPlainTextEdit()
        self._advanced_edit.setPlainText(json.dumps(existing_obj, indent=2))
        self._advanced_edit.setMinimumHeight(150)
        layout.addWidget(self._advanced_edit)

        # ---- Clear all button ---- #
        clear_btn = QPushButton("Clear All Overrides")
        clear_btn.clicked.connect(self._clear_all)
        layout.addWidget(clear_btn)

        # ---- Dialog buttons ---- #
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _clear_all(self) -> None:
        """Uncheck all sections and reset JSON to empty."""
        self._bg_check.setChecked(False)
        self._border_check.setChecked(False)
        self._title_check.setChecked(False)
        self._labels_check.setChecked(False)
        self._legend_check.setChecked(False)
        self._advanced_edit.setPlainText("{}")

    def _on_ok(self) -> None:
        """Validate and merge the result, then accept."""
        try:
            base = json.loads(self._advanced_edit.toPlainText().strip() or "{}")
            if not isinstance(base, dict):
                raise ValueError("must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            QMessageBox.warning(
                self, "Invalid JSON", f"Advanced JSON is not valid:\n{exc}"
            )
            return

        overrides: Dict[str, Any] = {}

        if self._bg_check.isChecked():
            overrides["background"] = build_background_object(
                True, self._bg_color.color(), self._bg_alpha.value()
            )
        if self._border_check.isChecked():
            overrides["border"] = build_border_object(True, self._border_color.color())
        if self._title_check.isChecked():
            overrides["title"] = build_title_object(
                True,
                self._title_font.currentFont().family(),
                self._title_size.value(),
                self._title_color.color(),
            )
        if self._labels_check.isChecked():
            overrides["labels"] = build_data_labels_object(
                True, self._labels_color.color(), self._labels_size.value()
            )
        if self._legend_check.isChecked():
            overrides["legend"] = build_legend_object(
                True, self._legend_pos.currentText(), self._legend_color.color()
            )

        self._result = merge_visual_style_entry(base, overrides)
        self.accept()

    def result_dict(self) -> Dict[str, Any]:
        """Return the merged result dict, or empty dict if dialog was cancelled."""
        return self._result or {}
