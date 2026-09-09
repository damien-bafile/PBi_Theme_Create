"""Dynamic visual formatter UI builder."""

from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .theme import TEXT_PRIMARY
from .widgets import ColorButton
from .visual_formatting_config import FormatField, FormatSection, get_formatting_sections


def balanced_columns(boxes, columns: int = 2) -> QHBoxLayout:
    """Lay *boxes* out across *columns* vertical columns, balancing height.

    Each box is placed in whichever column is currently shortest (estimated by
    its size hint), so a long list of group boxes forms a compact grid instead
    of one tall stack that overflows the screen.
    """
    col_layouts = [QVBoxLayout() for _ in range(max(1, columns))]
    heights = [0] * len(col_layouts)
    for box in boxes:
        i = heights.index(min(heights))
        col_layouts[i].addWidget(box)
        heights[i] += max(1, box.sizeHint().height())
    for col in col_layouts:
        col.addStretch(1)
    row = QHBoxLayout()
    for col in col_layouts:
        row.addLayout(col, 1)
    return row


class VisualFormatterPanel(QWidget):
    """Dynamic panel for formatting visual type options."""

    values_changed = Signal()  # Emitted whenever any value changes

    def __init__(self, visual_key: str, parent: QWidget | None = None,
                 max_columns: int = 2) -> None:
        super().__init__(parent)
        self._visual_key = visual_key
        self._max_columns = max(1, max_columns)
        self._field_widgets: Dict[str, Any] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        sections = get_formatting_sections(visual_key)
        if not sections:
            label = self.tr(f"No custom formatting available for this visual type")
            layout.addWidget(QWidget())  # Empty placeholder
            return

        # Build one group box per section...
        boxes = []
        style_labels = {"bold", "italic", "underline"}
        for section in sections:
            group = QGroupBox(section.name)
            form = QFormLayout(group)

            fields = section.fields
            i = 0
            while i < len(fields):
                field = fields[i]
                # Group a consecutive run of Bold/Italic/Underline toggles onto
                # one row (checkbox with its label underneath) to save height.
                if field.field_type == "boolean" and field.label.lower() in style_labels:
                    run = []
                    j = i
                    while (
                        j < len(fields)
                        and fields[j].field_type == "boolean"
                        and fields[j].label.lower() in style_labels
                    ):
                        run.append(fields[j])
                        j += 1
                    if len(run) >= 2:
                        form.addRow(self._build_style_row(run))
                        i = j
                        continue

                widget = self._create_widget_for_field(field)
                self._field_widgets[field.key] = widget
                form.addRow(field.label, widget)
                i += 1

            boxes.append(group)

        # ...then arrange them in balanced columns so tall visuals stay compact.
        # One column for a handful of sections (or when width is tight), two
        # once there are several and the caller allows it.
        columns = 2 if (len(boxes) > 3 and self._max_columns >= 2) else 1
        layout.addLayout(balanced_columns(boxes, columns))
        layout.addStretch()

    def _build_style_row(self, fields) -> QWidget:
        """Lay out font-style toggles (Bold/Italic/Underline) side by side,
        each checkbox centred with its label underneath."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(20)
        for field in fields:
            checkbox = self._create_widget_for_field(field)  # a QCheckBox
            self._field_widgets[field.key] = checkbox

            cell = QWidget()
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(2)
            cell_layout.addWidget(checkbox, 0, Qt.AlignHCenter)
            caption = QLabel(field.label)
            caption.setAlignment(Qt.AlignHCenter)
            cell_layout.addWidget(caption)
            row.addWidget(cell)
        row.addStretch(1)
        return container

    def _create_widget_for_field(self, field: FormatField) -> QWidget:
        """Create the appropriate widget for a formatting field."""
        if field.field_type == "color":
            button = ColorButton(field.default or "#FFFFFF", label=field.label)
            button.colorChanged.connect(self._on_field_changed)
            return button

        elif field.field_type == "boolean":
            checkbox = QCheckBox()
            checkbox.setChecked(bool(field.default))
            checkbox.toggled.connect(self._on_field_changed)
            return checkbox

        elif field.field_type == "number":
            spinbox = QSpinBox()
            spinbox.setMinimum(field.min_val or 0)
            spinbox.setMaximum(field.max_val or 100)
            if field.suffix:
                spinbox.setSuffix(f" {field.suffix}")
            spinbox.setValue(int(field.default or 0))
            spinbox.valueChanged.connect(self._on_field_changed)
            return spinbox

        elif field.field_type == "dropdown":
            combo = QComboBox()
            if field.options:
                for value, label in field.options:
                    combo.addItem(label, value)
            combo.currentIndexChanged.connect(self._on_field_changed)
            return combo

        elif field.field_type == "text":
            edit = QLineEdit()
            edit.setText(str(field.default or ""))
            edit.textChanged.connect(self._on_field_changed)
            return edit

        else:
            raise NotImplementedError(f"Field type {field.field_type} not implemented")

    def _on_field_changed(self) -> None:
        """Emit values_changed signal when any field changes."""
        self.values_changed.emit()

    def get_values(self) -> Dict[str, Any]:
        """Collect all formatting values from widgets."""
        values = {}
        for key, widget in self._field_widgets.items():
            if isinstance(widget, ColorButton):
                values[key] = widget.color()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentData()
            elif isinstance(widget, QLineEdit):
                values[key] = widget.text()
        return values

    def reset_to_defaults(self) -> None:
        """Reset every field to its configured default (used by Clear All Overrides)."""
        sections = get_formatting_sections(self._visual_key) or []
        for section in sections:
            for field in section.fields:
                widget = self._field_widgets.get(field.key)
                if widget is None:
                    continue
                if isinstance(widget, ColorButton):
                    widget.set_color(field.default or "#FFFFFF")
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(field.default))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(field.default or 0))
                elif isinstance(widget, QComboBox):
                    idx = widget.findData(field.default) if field.default is not None else 0
                    widget.setCurrentIndex(idx if idx >= 0 else 0)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(field.default or ""))
        self.values_changed.emit()

    def set_values(self, values: Dict[str, Any]) -> None:
        """Populate widgets from values dict."""
        for key, value in values.items():
            if key not in self._field_widgets:
                continue
            widget = self._field_widgets[key]

            if isinstance(widget, ColorButton):
                widget.set_color(str(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QComboBox):
                index = widget.findData(value)
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
