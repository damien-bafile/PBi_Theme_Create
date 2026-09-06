"""Modal dialog for editing per-visual style overrides."""

from __future__ import annotations

import copy
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
    QInputDialog,
)
from PySide6.QtSvgWidgets import QSvgWidget

from ..model import (
    PowerBITheme,
    LEGEND_POSITIONS,
    build_background_object,
    build_border_object,
    build_drop_shadow_object,
    build_visual_header_object,
    build_padding_object,
    build_title_object,
    build_data_labels_object,
    build_legend_object,
    unpack_background_object,
    unpack_border_object,
    unpack_drop_shadow_object,
    unpack_visual_header_object,
    unpack_padding_object,
    unpack_title_object,
    unpack_data_labels_object,
    unpack_legend_object,
    merge_visual_style_entry,
)
from .widgets import ColorButton
from .visual_formatter import VisualFormatterPanel
from .visual_formatting_config import is_visual_customizable
from .preview_mockups import render_visual_preview
from . import theme


class VisualStyleDialog(QDialog):
    """Edit structured and raw-JSON overrides for a single visual type's style."""

    #: label shown in the preset selector for the default ("*") style.
    DEFAULT_PRESET_LABEL = "Default (all visuals of this type)"

    def __init__(
        self,
        visual_key: str,
        visual_label: str,
        existing_obj: Dict[str, Any],
        parent: QWidget | None = None,
        pbi_theme: PowerBITheme | None = None,
        presets: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Edit {visual_label} Style")
        self.resize(1000, 650)
        self._visual_key = visual_key
        self._visual_label = visual_label
        self._theme = pbi_theme or PowerBITheme()
        self._result: Dict[str, Any] | None = None
        self._formatter_panel: VisualFormatterPanel | None = None
        self._preview_svg: QSvgWidget | None = None

        # Named style presets: {"*": default, "Preset A": {...}, ...}.
        self._presets: Dict[str, Any] = copy.deepcopy(presets) if presets else {"*": existing_obj or {}}
        if "*" not in self._presets:
            self._presets["*"] = {}
        self._current_preset: str = "*"
        existing_obj = self._presets.get("*", {})

        root_layout = QHBoxLayout(self)

        # ---- Left side: Tabs ---- #
        left_layout = QVBoxLayout()

        # Style preset selector
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Style preset:"))
        self._preset_combo = QComboBox()
        self._preset_combo.setAccessibleName("Style preset")
        preset_row.addWidget(self._preset_combo, 1)
        self._new_preset_btn = QPushButton("+ New")
        self._new_preset_btn.clicked.connect(self._on_new_preset)
        preset_row.addWidget(self._new_preset_btn)
        left_layout.addLayout(preset_row)

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
        self._border_width = QSpinBox()
        self._border_width.setRange(1, 10)
        self._border_width.setSuffix(" px")
        self._border_radius = QSpinBox()
        self._border_radius.setRange(0, 30)
        self._border_radius.setSuffix(" px")
        border_show, border_color, border_radius, border_width = unpack_border_object(existing_obj)
        self._border_color.set_color(border_color)
        self._border_radius.setValue(border_radius)
        self._border_width.setValue(border_width)
        border_layout.addRow(self._border_check, QLabel())
        border_layout.addRow("Color", self._border_color)
        border_layout.addRow("Width", self._border_width)
        border_layout.addRow("Rounded corners", self._border_radius)
        for w in (self._border_color, self._border_width, self._border_radius):
            self._border_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        generic_layout.addWidget(border_box)

        # ---- Drop shadow section ---- #
        shadow_box = QGroupBox("Drop Shadow")
        shadow_layout = QFormLayout(shadow_box)
        self._shadow_check = QCheckBox("Override")
        self._shadow_check.setAccessibleName("Override drop shadow")
        self._shadow_color = ColorButton(theme.TEXT_STRONG, label="Shadow color")
        shadow_show, shadow_color = unpack_drop_shadow_object(existing_obj)
        self._shadow_color.set_color(shadow_color)
        shadow_layout.addRow(self._shadow_check, QLabel())
        shadow_layout.addRow("Color", self._shadow_color)
        self._shadow_check.toggled.connect(lambda c: self._shadow_color.setEnabled(c))
        self._shadow_color.setEnabled(False)
        generic_layout.addWidget(shadow_box)

        # ---- Visual header section ---- #
        header_box = QGroupBox("Visual Header")
        header_layout = QFormLayout(header_box)
        self._vh_check = QCheckBox("Override")
        self._vh_check.setAccessibleName("Override visual header")
        self._vh_background = ColorButton(theme.SURFACE_BACKGROUND, label="Header background")
        self._vh_foreground = ColorButton(theme.TEXT_PRIMARY, label="Header icons")
        vh_show, vh_bg, vh_fg = unpack_visual_header_object(existing_obj)
        self._vh_background.set_color(vh_bg)
        self._vh_foreground.set_color(vh_fg)
        header_layout.addRow(self._vh_check, QLabel())
        header_layout.addRow("Background", self._vh_background)
        header_layout.addRow("Icons", self._vh_foreground)
        for w in (self._vh_background, self._vh_foreground):
            self._vh_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        generic_layout.addWidget(header_box)

        # ---- Padding section ---- #
        padding_box = QGroupBox("Padding")
        padding_layout = QFormLayout(padding_box)
        self._padding_check = QCheckBox("Override")
        self._padding_check.setAccessibleName("Override padding")
        self._padding_value = QSpinBox()
        self._padding_value.setRange(0, 40)
        self._padding_value.setSuffix(" px")
        self._padding_value.setValue(unpack_padding_object(existing_obj))
        padding_layout.addRow(self._padding_check, QLabel())
        padding_layout.addRow("All sides", self._padding_value)
        self._padding_check.toggled.connect(lambda c: self._padding_value.setEnabled(c))
        self._padding_value.setEnabled(False)
        generic_layout.addWidget(padding_box)

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

        # Live-update the preview whenever any generic override changes.
        for check in (
            self._bg_check, self._border_check, self._title_check,
            self._labels_check, self._legend_check, self._shadow_check,
            self._vh_check, self._padding_check,
        ):
            check.toggled.connect(self._update_preview)
        for color_btn in (
            self._bg_color, self._border_color, self._title_color,
            self._labels_color, self._legend_color, self._shadow_color,
            self._vh_background, self._vh_foreground,
        ):
            color_btn.colorChanged.connect(self._update_preview)
        self._border_width.valueChanged.connect(self._update_preview)
        self._border_radius.valueChanged.connect(self._update_preview)
        self._padding_value.valueChanged.connect(self._update_preview)
        self._bg_alpha.valueChanged.connect(self._update_preview)
        self._title_font.currentFontChanged.connect(self._update_preview)
        self._title_size.valueChanged.connect(self._update_preview)
        self._labels_size.valueChanged.connect(self._update_preview)
        self._legend_pos.currentIndexChanged.connect(self._update_preview)

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
        if self._formatter_panel:
            if existing_obj:
                formatting = existing_obj.get("formatting", {})
                if formatting:
                    self._formatter_panel.set_values(formatting)
            # Connect formatter changes to preview updates
            self._formatter_panel.values_changed.connect(self._update_preview)

        # Populate the preset selector now that every widget exists.
        self._refresh_preset_combo()
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        # Initial preview update
        self._update_preview()

        # Set initial focus to first tab
        tabs.setFocus()

    # ------------------------------------------------------------------ #
    # Style presets
    # ------------------------------------------------------------------ #
    def _refresh_preset_combo(self) -> None:
        self._preset_combo.blockSignals(True)
        self._preset_combo.clear()
        for name in self._presets:
            label = self.DEFAULT_PRESET_LABEL if name == "*" else name
            self._preset_combo.addItem(label, name)
        idx = self._preset_combo.findData(self._current_preset)
        if idx >= 0:
            self._preset_combo.setCurrentIndex(idx)
        self._preset_combo.blockSignals(False)

    def _current_style(self) -> Dict[str, Any]:
        """Build the style object represented by the fields right now."""
        try:
            base = json.loads(self._advanced_edit.toPlainText().strip() or "{}")
            if not isinstance(base, dict):
                base = {}
        except (json.JSONDecodeError, ValueError):
            base = {}
        return merge_visual_style_entry(base, self._build_overrides())

    def _apply_style(self, style_obj: Dict[str, Any]) -> None:
        """Populate every field from *style_obj* (mirrors the initial load)."""
        style_obj = style_obj or {}
        if self._formatter_panel:
            self._formatter_panel.set_values(style_obj.get("formatting", {}))
        _, bg_color, bg_trans = unpack_background_object(style_obj)
        self._bg_color.set_color(bg_color)
        self._bg_alpha.setValue(bg_trans)
        _, b_color, b_radius, b_width = unpack_border_object(style_obj)
        self._border_color.set_color(b_color)
        self._border_radius.setValue(b_radius)
        self._border_width.setValue(b_width)
        _, s_color = unpack_drop_shadow_object(style_obj)
        self._shadow_color.set_color(s_color)
        _, t_font, t_size, t_color = unpack_title_object(style_obj)
        self._title_font.setCurrentText(t_font)
        self._title_size.setValue(t_size)
        self._title_color.set_color(t_color)
        _, l_color, l_size = unpack_data_labels_object(style_obj)
        self._labels_color.set_color(l_color)
        self._labels_size.setValue(l_size)
        _, lg_pos, lg_color = unpack_legend_object(style_obj)
        self._legend_pos.setCurrentText(lg_pos)
        self._legend_color.set_color(lg_color)
        _, vh_bg, vh_fg = unpack_visual_header_object(style_obj)
        self._vh_background.set_color(vh_bg)
        self._vh_foreground.set_color(vh_fg)
        self._padding_value.setValue(unpack_padding_object(style_obj))
        for chk in (
            self._bg_check, self._border_check, self._shadow_check, self._title_check,
            self._labels_check, self._legend_check, self._vh_check, self._padding_check,
        ):
            chk.setChecked(False)
        self._advanced_edit.setPlainText(json.dumps(style_obj, indent=2))

    def _on_preset_changed(self, index: int) -> None:
        name = self._preset_combo.itemData(index)
        if name is None or name == self._current_preset:
            return
        self._presets[self._current_preset] = self._current_style()
        self._current_preset = name
        self._apply_style(self._presets.get(name, {}))
        self._update_preview()

    def _on_new_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "New style preset", "Preset name:")
        name = (name or "").strip()
        if not ok or not name:
            return
        if name == "*" or name == self.DEFAULT_PRESET_LABEL or name in self._presets:
            QMessageBox.warning(self, "Invalid name", "Choose a unique preset name (not 'Default').")
            return
        # Save the current preset, then seed the new one from the current fields.
        self._presets[self._current_preset] = self._current_style()
        self._presets[name] = self._current_style()
        self._current_preset = name
        self._refresh_preset_combo()

    def result_presets(self) -> Dict[str, Any]:
        """Return the full {presetName: styleObj} map (default plus named presets)."""
        return getattr(self, "_result_presets", None) or {"*": self.result_dict()}

    def _clear_all(self) -> None:
        """Uncheck all sections and reset JSON to empty."""
        self._bg_check.setChecked(False)
        self._border_check.setChecked(False)
        self._title_check.setChecked(False)
        self._labels_check.setChecked(False)
        self._legend_check.setChecked(False)
        self._shadow_check.setChecked(False)
        self._vh_check.setChecked(False)
        self._padding_check.setChecked(False)
        self._advanced_edit.setPlainText("{}")

    def _build_overrides(self) -> Dict[str, Any]:
        """Collect the current formatting + generic overrides into one dict.

        Shared by :meth:`_on_ok` (what gets saved) and :meth:`_update_preview`
        (what gets rendered), so the live preview always matches the result.
        """
        overrides: Dict[str, Any] = {}

        if self._formatter_panel:
            formatter_values = self._formatter_panel.get_values()
            if formatter_values:
                overrides["formatting"] = formatter_values

        if self._bg_check.isChecked():
            overrides["background"] = build_background_object(
                True, self._bg_color.color(), self._bg_alpha.value()
            )
        if self._border_check.isChecked():
            overrides["border"] = build_border_object(
                True, self._border_color.color(),
                self._border_radius.value(), self._border_width.value(),
            )
        if self._shadow_check.isChecked():
            overrides["dropShadow"] = build_drop_shadow_object(True, self._shadow_color.color())
        if self._vh_check.isChecked():
            overrides["visualHeader"] = build_visual_header_object(
                True, self._vh_background.color(), self._vh_foreground.color()
            )
        if self._padding_check.isChecked():
            overrides["padding"] = build_padding_object(self._padding_value.value())
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
        return overrides

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

        # Save the preset currently being edited, then expose the full map.
        self._presets[self._current_preset] = merge_visual_style_entry(base, self._build_overrides())
        self._result = self._presets.get("*", {})
        # Keep the default plus any non-empty named presets.
        self._result_presets = {
            name: obj for name, obj in self._presets.items() if obj or name == "*"
        }
        self.accept()

    def result_dict(self) -> Dict[str, Any]:
        """Return the merged result dict, or empty dict if dialog was cancelled."""
        return self._result or {}

    def _update_preview(self) -> None:
        """Re-render the live preview from the *exact* overrides that will be saved."""
        if not self._preview_svg:
            return

        # Render from a style object built the same way _on_ok builds the result,
        # so the preview reflects both visual formatting and generic overrides.
        style_obj = merge_visual_style_entry({}, self._build_overrides())
        svg_data = render_visual_preview(
            self._theme, self._visual_key, style_obj, width=250, height=200
        )
        if svg_data:
            self._preview_svg.load(QByteArray(svg_data.encode("utf-8")))
