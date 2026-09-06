"""Modal dialog for editing per-visual style overrides."""

from __future__ import annotations

import json
from typing import Any, Dict

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
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
    QTabWidget,
    QScrollArea,
    QFontComboBox,
)
from PySide6.QtSvgWidgets import QSvgWidget

from ..model import (
    PowerBITheme,
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
from .visual_formatter import VisualFormatterPanel
from .visual_formatting_config import is_visual_customizable
from .preview_mockups import generate_table_svg, generate_bar_chart_svg
from . import theme


class VisualStyleDialog(QDialog):
    """Edit structured and raw-JSON overrides for a single visual type's style."""

    def __init__(
        self,
        visual_key: str,
        visual_label: str,
        existing_obj: Dict[str, Any],
        parent: QWidget | None = None,
        theme: PowerBITheme | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Edit {visual_label} Style")
        self.resize(1000, 650)
        self._visual_key = visual_key
        self._visual_label = visual_label
        self._theme = theme or PowerBITheme()
        self._result: Dict[str, Any] | None = None
        self._formatter_panel: VisualFormatterPanel | None = None
        self._preview_svg: QSvgWidget | None = None

        root_layout = QHBoxLayout(self)

        # ---- Left side: Tabs ---- #
        left_layout = QVBoxLayout()

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Visual-specific formatting (if available)
        if is_visual_customizable(visual_key):
            self._formatter_panel = VisualFormatterPanel(visual_key)
            tabs.addTab(self._formatter_panel, "Visual Formatting")

        # Tab 2: Generic overrides
        generic_widget = QWidget()
        generic_layout = QVBoxLayout(generic_widget)

        # ---- Background section ---- #
        bg_box = QGroupBox("Background")
        bg_layout = QFormLayout(bg_box)
        self._bg_check = QCheckBox("Override")
        self._bg_check.setAccessibleName("Override background")
        self._bg_check.setAccessibleDescription("Check to customize background color and transparency")
        self._bg_color = ColorButton(theme.SURFACE_BACKGROUND, label="Background color")
        self._bg_alpha = QSpinBox()
        self._bg_alpha.setRange(0, 100)
        self._bg_alpha.setSuffix("%")
        self._bg_alpha.setAccessibleName("Background transparency")
        self._bg_alpha.setAccessibleDescription("0 is fully transparent, 100 is fully opaque")
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
        generic_layout.addWidget(bg_box)

        # ---- Border section ---- #
        border_box = QGroupBox("Border")
        border_layout = QFormLayout(border_box)
        self._border_check = QCheckBox("Override")
        self._border_check.setAccessibleName("Override border")
        self._border_color = ColorButton(theme.TEXT_STRONG, label="Border color")
        border_show, border_color = unpack_border_object(existing_obj)
        self._border_color.set_color(border_color)
        border_layout.addRow(self._border_check, QLabel())
        border_layout.addRow("Color", self._border_color)
        self._border_check.toggled.connect(lambda c: self._border_color.setEnabled(c))
        self._border_color.setEnabled(False)
        generic_layout.addWidget(border_box)

        # ---- Title section ---- #
        title_box = QGroupBox("Title")
        title_layout = QFormLayout(title_box)
        self._title_check = QCheckBox("Override")
        self._title_font = QFontComboBox()
        self._title_size = QSpinBox()
        self._title_size.setRange(4, 120)
        self._title_size.setSuffix(" pt")
        self._title_color = ColorButton(theme.TEXT_PRIMARY)
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
        generic_layout.addWidget(title_box)

        # ---- Data labels section ---- #
        labels_box = QGroupBox("Data Labels")
        labels_layout = QFormLayout(labels_box)
        self._labels_check = QCheckBox("Override")
        self._labels_color = ColorButton(theme.TEXT_PRIMARY)
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
        generic_layout.addWidget(labels_box)

        # ---- Legend section ---- #
        legend_box = QGroupBox("Legend")
        legend_layout = QFormLayout(legend_box)
        self._legend_check = QCheckBox("Override")
        self._legend_pos = QComboBox()
        self._legend_pos.addItems(LEGEND_POSITIONS)
        self._legend_color = ColorButton(theme.TEXT_PRIMARY)
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
        generic_layout.addWidget(legend_box)
        generic_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(generic_widget)
        scroll.setWidgetResizable(True)
        tabs.addTab(scroll, "Generic Overrides")

        # Tab 3: Advanced JSON
        advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(advanced_widget)
        advanced_layout.addWidget(QLabel("Raw styleName '*' object:"))
        self._advanced_edit = QPlainTextEdit()
        self._advanced_edit.setPlainText(json.dumps(existing_obj, indent=2))
        advanced_layout.addWidget(self._advanced_edit)
        tabs.addTab(advanced_widget, "Advanced JSON")

        left_layout.addWidget(tabs)

        # ---- Clear all button ---- #
        clear_btn = QPushButton("Clear All Overrides")
        clear_btn.clicked.connect(self._clear_all)
        left_layout.addWidget(clear_btn)

        # ---- Dialog buttons ---- #
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Ok).setDefault(True)
        left_layout.addWidget(buttons)

        # ---- Right side: Preview ---- #
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Live Preview:"))
        right_layout.addWidget(QLabel(f"{visual_label}", ), )

        self._preview_svg = QSvgWidget()
        self._preview_svg.setMinimumSize(250, 250)
        self._preview_svg.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; background: white;")
        right_layout.addWidget(self._preview_svg)
        right_layout.addStretch()

        # Add left and right to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMinimumWidth(450)

        root_layout.addWidget(left_widget, 1)
        root_layout.addLayout(right_layout, 0)

        # Load existing formatting values if available
        if self._formatter_panel and existing_obj:
            formatting = existing_obj.get("formatting", {})
            if formatting:
                self._formatter_panel.set_values(formatting)
            # Connect formatter changes to preview updates
            self._formatter_panel.values_changed.connect(self._update_preview)

        # Initial preview update
        self._update_preview()

        # Set initial focus to first tab
        tabs.setFocus()

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

        # Collect visual-specific formatting if available
        if self._formatter_panel:
            formatter_values = self._formatter_panel.get_values()
            if formatter_values:
                overrides["formatting"] = formatter_values

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

    def _update_preview(self) -> None:
        """Update the preview to show the current formatting options."""
        if not self._preview_svg:
            return

        # Get current formatting values from formatter panel
        formatting = {}
        if self._formatter_panel:
            formatting = self._formatter_panel.get_values()

        # Generate appropriate preview based on visual type
        svg_data = ""
        if self._visual_key in ("matrix", "table", "tableEx", "pivotTable"):
            # Table preview
            visual_styles = {"*": {"formatting": formatting}}
            svg_data = generate_table_svg(self._theme, visual_styles, width=250, height=180)
        elif self._visual_key in ("barChart", "columnChart", "lineChart", "pieChart", "gauge", "card", "kpi"):
            # For charts, show a simpler bar chart with formatting
            visual_styles = {"*": {"formatting": formatting}}
            svg_data = generate_bar_chart_svg(self._theme, width=250, height=180)
        else:
            # Default preview
            svg_data = generate_bar_chart_svg(self._theme, width=250, height=180)

        # Load SVG into widget
        if svg_data:
            svg_bytes = QByteArray(svg_data.encode("utf-8"))
            self._preview_svg.load(svg_bytes)
