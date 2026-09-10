"""Modal dialog for editing per-visual style overrides."""

from __future__ import annotations

import copy
import json
from typing import Any, Dict

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QGuiApplication, QShortcut, QKeySequence
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
    QLineEdit,
)
from PySide6.QtSvgWidgets import QSvgWidget

from ..model import (
    PowerBITheme,
    LEGEND_POSITIONS,
    build_background_object,
    build_border_object,
    build_drop_shadow_object,
    build_visual_header_object,
    build_subtitle_object,
    build_padding_object,
    build_divider_object,
    build_spacing_object,
    build_general_object,
    build_visual_tooltip_object,
    build_visual_header_tooltip_object,
    build_title_object,
    build_data_labels_object,
    build_legend_object,
    unpack_background_object,
    unpack_border_object,
    unpack_drop_shadow_object,
    unpack_visual_header_object,
    unpack_subtitle_object,
    unpack_padding_object,
    unpack_divider_object,
    unpack_spacing_object,
    unpack_general_object,
    unpack_visual_tooltip_object,
    unpack_visual_header_tooltip_object,
    unpack_title_object,
    unpack_data_labels_object,
    unpack_legend_object,
    merge_visual_style_entry,
)
from .widgets import ColorButton
from .visual_formatter import VisualFormatterPanel, balanced_columns
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
        # Open at a comfortable size but never larger than the screen, so the
        # dialog always fits (some visuals have many formatting sections).
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        if avail:
            width = min(1000, avail.width() - 80)
            height = min(720, avail.height() - 80)
            self.setMaximumSize(avail.width(), avail.height())
        else:  # headless / no screen
            width, height = 1000, 720
        self.resize(max(600, width), max(400, height))
        # Two columns of sections only when the left pane (dialog width minus the
        # ~300px preview column) can hold two ~350px section columns; otherwise one
        # column that scrolls vertically (never off-screen).
        PREVIEW_COLUMN_PX, TWO_SECTION_COLUMNS_PX = 300, 700
        self._section_columns = 2 if (width - PREVIEW_COLUMN_PX) >= TWO_SECTION_COLUMNS_PX else 1
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
        # If the visual had no overrides on open, an untouched OK must NOT mark it
        # "customized" — the ✓ badge should mean the user actually changed something.
        self._existing_was_empty = not bool(existing_obj)
        self._user_touched = False
        # In-dialog undo/redo (Ctrl+Z / Ctrl+Y) over the field state.
        self._undo_stack: list[Dict[str, Any]] = []
        self._redo_stack: list[Dict[str, Any]] = []
        self._undo_baseline: Dict[str, Any] | None = None
        self._restoring = False
        self._undo_ready = False
        self._undo_widgets: list = []

        root_layout = QHBoxLayout(self)

        # ---- Left side: Tabs ---- #
        left_layout = QVBoxLayout()

        # Style preset selector
        preset_row = QHBoxLayout()
        _preset_tip = (
            "Style presets map to Power BI's named styleName entries for this "
            "visual. “Default” (*) applies to every instance; “+ New” adds a "
            "named preset users can pick from the visual's Style dropdown."
        )
        preset_lbl = QLabel("Style preset:")
        preset_lbl.setToolTip(_preset_tip)
        preset_row.addWidget(preset_lbl)
        self._preset_combo = QComboBox()
        self._preset_combo.setAccessibleName("Style preset")
        self._preset_combo.setToolTip(_preset_tip)
        preset_row.addWidget(self._preset_combo, 1)
        self._new_preset_btn = QPushButton("+ New")
        self._new_preset_btn.setToolTip(_preset_tip)
        self._new_preset_btn.clicked.connect(self._on_new_preset)
        preset_row.addWidget(self._new_preset_btn)
        left_layout.addLayout(preset_row)

        # Tabs
        tabs = QTabWidget()
        # Show all three tab labels instead of clipping them behind scroll chevrons.
        tabs.setUsesScrollButtons(False)
        tabs.tabBar().setExpanding(True)

        # Tab 1: Visual-specific formatting (if available), inside a scroll area
        # so visuals with many sections never force the dialog off-screen.
        if is_visual_customizable(visual_key):
            self._formatter_panel = VisualFormatterPanel(
                visual_key, max_columns=self._section_columns
            )
            # Make the override model explicit: unlike the Generic Overrides tab
            # (opt-in per section), these fields export together once the visual is
            # customized. The live preview + JSON show exactly what will be written.
            fmt_container = QWidget()
            fmt_v = QVBoxLayout(fmt_container)
            fmt_v.setContentsMargins(0, 0, 0, 0)
            fmt_note = QLabel(
                "These settings are written as a set when this visual is customized. "
                "Use “Clear All Overrides” to return everything to defaults."
            )
            fmt_note.setWordWrap(True)
            fmt_note.setStyleSheet("color: #605E5C; padding: 4px 2px;")
            fmt_v.addWidget(fmt_note)
            formatter_scroll = QScrollArea()
            formatter_scroll.setWidget(self._formatter_panel)
            formatter_scroll.setWidgetResizable(True)
            fmt_v.addWidget(formatter_scroll, 1)
            tabs.addTab(fmt_container, "Visual Formatting")

        # Tab 2: Generic overrides. Sections are collected into a list and then
        # arranged in balanced columns so the tab stays compact.
        generic_widget = QWidget()
        generic_layout = QVBoxLayout(generic_widget)
        _generic_boxes = []

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
        _generic_boxes.append(bg_box)

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
        _generic_boxes.append(border_box)

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
        _generic_boxes.append(shadow_box)

        # ---- Subtitle section ---- #
        subtitle_box = QGroupBox("Subtitle")
        subtitle_layout = QFormLayout(subtitle_box)
        self._subtitle_check = QCheckBox("Override")
        self._subtitle_check.setAccessibleName("Override subtitle")
        self._subtitle_text = QLineEdit()
        self._subtitle_color = ColorButton(theme.TEXT_PRIMARY, label="Subtitle color")
        self._subtitle_size = QSpinBox()
        self._subtitle_size.setRange(6, 40)
        self._subtitle_size.setSuffix(" pt")
        sub_show, sub_text, sub_color, sub_size = unpack_subtitle_object(existing_obj)
        self._subtitle_text.setText(sub_text)
        self._subtitle_color.set_color(sub_color)
        self._subtitle_size.setValue(sub_size)
        subtitle_layout.addRow(self._subtitle_check, QLabel())
        subtitle_layout.addRow("Text", self._subtitle_text)
        subtitle_layout.addRow("Color", self._subtitle_color)
        subtitle_layout.addRow("Size", self._subtitle_size)
        for w in (self._subtitle_text, self._subtitle_color, self._subtitle_size):
            self._subtitle_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        _generic_boxes.append(subtitle_box)

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
        _generic_boxes.append(header_box)

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
        _generic_boxes.append(padding_box)

        # ---- Divider section ---- #
        divider_box = QGroupBox("Divider")
        divider_layout = QFormLayout(divider_box)
        self._divider_check = QCheckBox("Override")
        self._divider_check.setAccessibleName("Override divider")
        self._divider_color = ColorButton("#D0D0D0", label="Divider color")
        self._divider_width = QSpinBox()
        self._divider_width.setRange(1, 10)
        self._divider_width.setSuffix(" px")
        self._divider_style = QComboBox()
        self._divider_style.addItems(["solid", "dashed", "dotted"])
        d_show, d_color, d_width, d_style = unpack_divider_object(existing_obj)
        self._divider_color.set_color(d_color)
        self._divider_width.setValue(d_width)
        self._divider_style.setCurrentText(d_style)
        divider_layout.addRow(self._divider_check, QLabel())
        divider_layout.addRow("Color", self._divider_color)
        divider_layout.addRow("Width", self._divider_width)
        divider_layout.addRow("Style", self._divider_style)
        for w in (self._divider_color, self._divider_width, self._divider_style):
            self._divider_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        _generic_boxes.append(divider_box)

        # ---- Spacing section (export-only) ---- #
        spacing_box = QGroupBox("Spacing")
        spacing_layout = QFormLayout(spacing_box)
        self._spacing_check = QCheckBox("Override")
        self._spacing_check.setAccessibleName("Override spacing")
        self._spacing_below_title = QSpinBox()
        self._spacing_below_title.setRange(0, 40)
        self._spacing_below_title.setSuffix(" px")
        self._spacing_vertical = QSpinBox()
        self._spacing_vertical.setRange(0, 40)
        self._spacing_vertical.setSuffix(" px")
        _, sp_below, sp_vert = unpack_spacing_object(existing_obj)
        self._spacing_below_title.setValue(sp_below)
        self._spacing_vertical.setValue(sp_vert)
        spacing_layout.addRow(self._spacing_check, QLabel())
        spacing_layout.addRow("Below title", self._spacing_below_title)
        spacing_layout.addRow("Between rows", self._spacing_vertical)
        for w in (self._spacing_below_title, self._spacing_vertical):
            self._spacing_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        _generic_boxes.append(spacing_box)

        # ---- General (alt text / responsive) section (export-only) ---- #
        general_box = QGroupBox("General")
        general_layout = QFormLayout(general_box)
        self._general_check = QCheckBox("Override")
        self._general_check.setAccessibleName("Override general")
        self._general_alt = QLineEdit()
        self._general_keep_order = QCheckBox("Keep layer order (responsive)")
        g_alt, g_keep = unpack_general_object(existing_obj)
        self._general_alt.setText(g_alt)
        self._general_keep_order.setChecked(g_keep)
        general_layout.addRow(self._general_check, QLabel())
        general_layout.addRow("Alt text", self._general_alt)
        general_layout.addRow("", self._general_keep_order)
        for w in (self._general_alt, self._general_keep_order):
            self._general_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        _generic_boxes.append(general_box)

        # ---- Data tooltip section (export-only) ---- #
        tooltip_box = QGroupBox("Data Tooltip")
        tooltip_layout = QFormLayout(tooltip_box)
        self._tooltip_check = QCheckBox("Override")
        self._tooltip_check.setAccessibleName("Override data tooltip")
        self._tooltip_bg = ColorButton(theme.SURFACE_BACKGROUND, label="Tooltip background")
        self._tooltip_title = ColorButton(theme.TEXT_PRIMARY, label="Tooltip title color")
        self._tooltip_value = ColorButton(theme.TEXT_PRIMARY, label="Tooltip value color")
        tt_bg, tt_title, tt_value, _tt_trans = unpack_visual_tooltip_object(existing_obj)
        self._tooltip_bg.set_color(tt_bg)
        self._tooltip_title.set_color(tt_title)
        self._tooltip_value.set_color(tt_value)
        tooltip_layout.addRow(self._tooltip_check, QLabel())
        tooltip_layout.addRow("Background", self._tooltip_bg)
        tooltip_layout.addRow("Title", self._tooltip_title)
        tooltip_layout.addRow("Value", self._tooltip_value)
        for w in (self._tooltip_bg, self._tooltip_title, self._tooltip_value):
            self._tooltip_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        _generic_boxes.append(tooltip_box)

        # ---- Header tooltip section (export-only) ---- #
        htooltip_box = QGroupBox("Header Tooltip")
        htooltip_layout = QFormLayout(htooltip_box)
        self._htooltip_check = QCheckBox("Override")
        self._htooltip_check.setAccessibleName("Override header tooltip")
        self._htooltip_bg = ColorButton(theme.SURFACE_BACKGROUND, label="Header tooltip background")
        self._htooltip_title = ColorButton(theme.TEXT_PRIMARY, label="Header tooltip title color")
        ht_bg, ht_title, _ht_trans = unpack_visual_header_tooltip_object(existing_obj)
        self._htooltip_bg.set_color(ht_bg)
        self._htooltip_title.set_color(ht_title)
        htooltip_layout.addRow(self._htooltip_check, QLabel())
        htooltip_layout.addRow("Background", self._htooltip_bg)
        htooltip_layout.addRow("Title", self._htooltip_title)
        for w in (self._htooltip_bg, self._htooltip_title):
            self._htooltip_check.toggled.connect(lambda c, _w=w: _w.setEnabled(c))
            w.setEnabled(False)
        _generic_boxes.append(htooltip_box)

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
        _generic_boxes.append(title_box)

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
        _generic_boxes.append(labels_box)

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
        _generic_boxes.append(legend_box)
        generic_layout.addLayout(balanced_columns(_generic_boxes, self._section_columns))
        generic_layout.addStretch()

        # Progressive disclosure: collapse each override section to just its
        # "Override" checkbox until it's enabled, so the tab isn't a wall of 14
        # expanded sections (and it reinforces what "override" means here).
        for _box in _generic_boxes:
            _form = _box.layout()
            if not isinstance(_form, QFormLayout):
                continue
            # Tight margins so a collapsed section reads as a slim row, not a big
            # empty box.
            _form.setContentsMargins(8, 4, 8, 4)
            _form.setVerticalSpacing(4)
            _check = None
            _check_row = 0
            for _r in range(_form.rowCount()):
                for _role in (QFormLayout.LabelRole, QFormLayout.FieldRole):
                    _it = _form.itemAt(_r, _role)
                    _w = _it.widget() if _it else None
                    if isinstance(_w, QCheckBox):
                        _check, _check_row = _w, _r
                        break
                if _check is not None:
                    break
            if _check is None:
                continue

            def _toggler(checked, form=_form, first=_check_row + 1, total=_form.rowCount()):
                for _rr in range(first, total):
                    form.setRowVisible(_rr, checked)

            _check.toggled.connect(_toggler)
            _toggler(_check.isChecked())  # start collapsed

        # Live-update the preview whenever any generic override changes.
        for check in (
            self._bg_check, self._border_check, self._title_check,
            self._labels_check, self._legend_check, self._shadow_check,
            self._vh_check, self._padding_check, self._subtitle_check,
            self._divider_check, self._spacing_check, self._general_check,
            self._tooltip_check, self._htooltip_check,
        ):
            check.toggled.connect(self._update_preview)
            check.toggled.connect(self._note_touch)
        for color_btn in (
            self._bg_color, self._border_color, self._title_color,
            self._labels_color, self._legend_color, self._shadow_color,
            self._vh_background, self._vh_foreground, self._subtitle_color,
            self._divider_color, self._tooltip_bg, self._tooltip_title,
            self._tooltip_value, self._htooltip_bg, self._htooltip_title,
        ):
            color_btn.colorChanged.connect(self._update_preview)
            color_btn.colorChanged.connect(self._note_touch)
        for _w in (self._border_width, self._border_radius, self._padding_value,
                   self._subtitle_size, self._bg_alpha, self._title_size,
                   self._labels_size, self._divider_width):
            _w.valueChanged.connect(self._update_preview)
            _w.valueChanged.connect(self._note_touch)
        self._subtitle_text.textChanged.connect(self._update_preview)
        self._subtitle_text.textChanged.connect(self._note_touch)
        self._title_font.currentFontChanged.connect(self._update_preview)
        self._title_font.currentFontChanged.connect(self._note_touch)
        self._legend_pos.currentIndexChanged.connect(self._update_preview)
        self._legend_pos.currentIndexChanged.connect(self._note_touch)
        self._divider_style.currentIndexChanged.connect(self._update_preview)
        self._divider_style.currentIndexChanged.connect(self._note_touch)
        self._general_alt.textChanged.connect(self._note_touch)
        self._general_keep_order.toggled.connect(self._note_touch)
        self._spacing_below_title.valueChanged.connect(self._note_touch)
        self._spacing_vertical.valueChanged.connect(self._note_touch)

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
        # Editing the raw JSON counts as a user change (connect after the initial set).
        self._advanced_edit.textChanged.connect(self._note_touch)
        advanced_layout.addWidget(self._advanced_edit)
        tabs.addTab(advanced_widget, "Advanced JSON")

        left_layout.addWidget(tabs)

        # ---- Undo / Redo + Clear all ---- #
        action_row = QHBoxLayout()
        self._undo_btn = QPushButton("↶ Undo")
        self._undo_btn.setToolTip("Undo (Ctrl+Z)")
        self._undo_btn.clicked.connect(self._undo_dialog)
        self._redo_btn = QPushButton("↷ Redo")
        self._redo_btn.setToolTip("Redo (Ctrl+Y)")
        self._redo_btn.clicked.connect(self._redo_dialog)
        action_row.addWidget(self._undo_btn)
        action_row.addWidget(self._redo_btn)
        action_row.addStretch(1)
        clear_btn = QPushButton("Clear All Overrides")
        clear_btn.clicked.connect(self._on_clear_all_clicked)
        action_row.addWidget(clear_btn)
        left_layout.addLayout(action_row)

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
        self._preview_svg.setStyleSheet(f"border: 1px solid {theme.BORDER_HAIRLINE}; border-radius: 4px; background: white;")
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
            self._formatter_panel.values_changed.connect(self._note_touch)

        # Populate the preset selector now that every widget exists.
        self._refresh_preset_combo()
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        # Initial preview update
        self._update_preview()

        # ---- In-dialog undo/redo ---- #
        # Register every field so a snapshot captures the full dialog state.
        self._undo_widgets = [
            self._bg_check, self._bg_color, self._bg_alpha,
            self._border_check, self._border_color, self._border_width, self._border_radius,
            self._shadow_check, self._shadow_color,
            self._title_check, self._title_font, self._title_size, self._title_color,
            self._labels_check, self._labels_color, self._labels_size,
            self._legend_check, self._legend_pos, self._legend_color,
            self._vh_check, self._vh_background, self._vh_foreground,
            self._padding_check, self._padding_value,
            self._subtitle_check, self._subtitle_text, self._subtitle_color, self._subtitle_size,
            self._divider_check, self._divider_color, self._divider_width, self._divider_style,
            self._spacing_check, self._spacing_below_title, self._spacing_vertical,
            self._general_check, self._general_alt, self._general_keep_order,
            self._tooltip_check, self._tooltip_bg, self._tooltip_title, self._tooltip_value,
            self._htooltip_check, self._htooltip_bg, self._htooltip_title,
        ]
        self._undo_baseline = self._snapshot()
        self._undo_ready = True
        self._update_dialog_undo_actions()
        for _seq, _slot in (
            (QKeySequence.Undo, self._undo_dialog),
            (QKeySequence.Redo, self._redo_dialog),
            (QKeySequence("Ctrl+Y"), self._redo_dialog),
        ):
            _sc = QShortcut(_seq, self)
            _sc.activated.connect(_slot)

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
        _, sub_text, sub_color, sub_size = unpack_subtitle_object(style_obj)
        self._subtitle_text.setText(sub_text)
        self._subtitle_color.set_color(sub_color)
        self._subtitle_size.setValue(sub_size)
        _, d_color, d_width, d_style = unpack_divider_object(style_obj)
        self._divider_color.set_color(d_color)
        self._divider_width.setValue(d_width)
        self._divider_style.setCurrentText(d_style)
        _, sp_below, sp_vert = unpack_spacing_object(style_obj)
        self._spacing_below_title.setValue(sp_below)
        self._spacing_vertical.setValue(sp_vert)
        g_alt, g_keep = unpack_general_object(style_obj)
        self._general_alt.setText(g_alt)
        self._general_keep_order.setChecked(g_keep)
        tt_bg, tt_title, tt_value, _ = unpack_visual_tooltip_object(style_obj)
        self._tooltip_bg.set_color(tt_bg)
        self._tooltip_title.set_color(tt_title)
        self._tooltip_value.set_color(tt_value)
        ht_bg, ht_title, _ = unpack_visual_header_tooltip_object(style_obj)
        self._htooltip_bg.set_color(ht_bg)
        self._htooltip_title.set_color(ht_title)
        for chk in (
            self._bg_check, self._border_check, self._shadow_check, self._title_check,
            self._labels_check, self._legend_check, self._vh_check, self._padding_check,
            self._subtitle_check, self._divider_check, self._spacing_check,
            self._general_check, self._tooltip_check, self._htooltip_check,
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

    def _on_clear_all_clicked(self) -> None:
        """Confirm before the destructive Clear All (there is no in-dialog undo)."""
        resp = QMessageBox.question(
            self, "Clear all overrides?",
            "Reset every override for this visual back to defaults? "
            "You can undo this with Ctrl+Z.",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel,
        )
        if resp == QMessageBox.Yes:
            self._clear_all()

    def _clear_all(self) -> None:
        """Uncheck all sections and reset JSON/formatting to defaults (one undo step)."""
        # Suppress per-widget history so the whole clear is a single Ctrl+Z step.
        was_restoring = self._restoring
        self._restoring = True
        try:
            self._clear_all_fields()
        finally:
            self._restoring = was_restoring
        self._record_dialog_history()
        self._update_preview()

    def _clear_all_fields(self) -> None:
        self._bg_check.setChecked(False)
        self._border_check.setChecked(False)
        self._title_check.setChecked(False)
        self._labels_check.setChecked(False)
        self._legend_check.setChecked(False)
        self._shadow_check.setChecked(False)
        self._vh_check.setChecked(False)
        self._padding_check.setChecked(False)
        self._subtitle_check.setChecked(False)
        self._divider_check.setChecked(False)
        self._spacing_check.setChecked(False)
        self._general_check.setChecked(False)
        self._tooltip_check.setChecked(False)
        self._htooltip_check.setChecked(False)
        # "All" must include the Visual Formatting tab, not just the generic
        # overrides — otherwise the Advanced JSON box no longer tells the truth.
        if self._formatter_panel:
            self._formatter_panel.reset_to_defaults()
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
        if self._divider_check.isChecked():
            overrides["divider"] = build_divider_object(
                True, self._divider_color.color(),
                self._divider_width.value(), self._divider_style.currentText(),
            )
        if self._spacing_check.isChecked():
            overrides["spacing"] = build_spacing_object(
                True, self._spacing_below_title.value(), self._spacing_vertical.value()
            )
        if self._general_check.isChecked():
            overrides["general"] = build_general_object(
                self._general_alt.text(), self._general_keep_order.isChecked()
            )
        if self._tooltip_check.isChecked():
            overrides["visualTooltip"] = build_visual_tooltip_object(
                self._tooltip_bg.color(), self._tooltip_title.color(),
                self._tooltip_value.color(), 0,
            )
        if self._htooltip_check.isChecked():
            overrides["visualHeaderTooltip"] = build_visual_header_tooltip_object(
                self._htooltip_bg.color(), self._htooltip_title.color(), 0
            )
        if self._subtitle_check.isChecked():
            overrides["subTitle"] = build_subtitle_object(
                True, self._subtitle_text.text(),
                self._subtitle_color.color(), self._subtitle_size.value(),
            )
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
        # A previously-empty visual opened and OK'd without any change stays
        # un-customized, so the checklist's ✓ means "the user changed something".
        if self._existing_was_empty and not self._user_touched:
            self._result = {}
            self._result_presets = {"*": {}}
            self.accept()
            return
        self._result = self._presets.get("*", {})
        # Keep the default plus any non-empty named presets.
        self._result_presets = {
            name: obj for name, obj in self._presets.items() if obj or name == "*"
        }
        self.accept()

    def result_dict(self) -> Dict[str, Any]:
        """Return the merged result dict, or empty dict if dialog was cancelled."""
        return self._result or {}

    def _note_touch(self, *args) -> None:
        """Record that the user actually changed a control (drives the ✓ badge)."""
        self._user_touched = True
        self._record_dialog_history()

    # ------------------------------------------------------------------ #
    # In-dialog undo / redo
    # ------------------------------------------------------------------ #
    @staticmethod
    def _capture_widget(w) -> Any:
        if isinstance(w, ColorButton):
            return w.color()
        if isinstance(w, QCheckBox):
            return w.isChecked()
        if isinstance(w, QSpinBox):
            return w.value()
        if isinstance(w, QFontComboBox):  # subclass of QComboBox — check first
            return w.currentText()
        if isinstance(w, QComboBox):
            return w.currentIndex()
        if isinstance(w, QLineEdit):
            return w.text()
        return None

    @staticmethod
    def _restore_widget(w, v) -> None:
        if isinstance(w, ColorButton):
            w.set_color(v)
        elif isinstance(w, QCheckBox):
            w.setChecked(bool(v))
        elif isinstance(w, QSpinBox):
            w.setValue(int(v))
        elif isinstance(w, QFontComboBox):
            w.setCurrentText(v)
        elif isinstance(w, QComboBox):
            w.setCurrentIndex(int(v))
        elif isinstance(w, QLineEdit):
            w.setText(v)

    def _snapshot(self) -> Dict[str, Any]:
        return {
            "formatting": dict(self._formatter_panel.get_values()) if self._formatter_panel else {},
            "generic": [self._capture_widget(w) for w in self._undo_widgets],
            "advanced": self._advanced_edit.toPlainText(),
        }

    def _restore(self, snap: Dict[str, Any]) -> None:
        self._restoring = True
        try:
            if self._formatter_panel:
                self._formatter_panel.reset_to_defaults()
                self._formatter_panel.set_values(snap.get("formatting", {}))
            for w, v in zip(self._undo_widgets, snap.get("generic", [])):
                self._restore_widget(w, v)
            self._advanced_edit.setPlainText(snap.get("advanced", "{}"))
        finally:
            self._restoring = False
        self._update_preview()

    def _update_dialog_undo_actions(self) -> None:
        if hasattr(self, "_undo_btn"):
            self._undo_btn.setEnabled(bool(self._undo_stack))
            self._redo_btn.setEnabled(bool(self._redo_stack))

    def _record_dialog_history(self) -> None:
        """Commit one undo step: push the pre-edit baseline, rebase to now."""
        if self._restoring or not self._undo_ready:
            return
        if self._undo_baseline is not None:
            self._undo_stack.append(self._undo_baseline)
            if len(self._undo_stack) > 100:
                self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._undo_baseline = self._snapshot()
        self._update_dialog_undo_actions()

    def _undo_dialog(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self._undo_baseline or self._snapshot())
        self._undo_baseline = self._undo_stack.pop()
        self._restore(self._undo_baseline)
        self._update_dialog_undo_actions()

    def _redo_dialog(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self._undo_baseline or self._snapshot())
        self._undo_baseline = self._redo_stack.pop()
        self._restore(self._undo_baseline)
        self._update_dialog_undo_actions()

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
            self._preview_svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
