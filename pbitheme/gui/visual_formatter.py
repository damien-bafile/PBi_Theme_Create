"""Dynamic visual formatter UI builder."""

from __future__ import annotations

from typing import Any, Callable, Dict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .theme import TEXT_PRIMARY
from .widgets import ColorButton
from .visual_formatting_config import FormatField, FormatSection, get_formatting_sections


class VisualFormatterPanel(QWidget):
    """Dynamic panel for formatting visual type options."""

    values_changed = Signal()  # Emitted whenever any value changes

    def __init__(self, visual_key: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._visual_key = visual_key
        self._field_widgets: Dict[str, Any] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        sections = get_formatting_sections(visual_key)
        if not sections:
            label = self.tr(f"No custom formatting available for this visual type")
            layout.addWidget(QWidget())  # Empty placeholder
            return

        # Build UI sections
        for section in sections:
            group = QGroupBox(section.name)
            form = QFormLayout(group)

            for field in section.fields:
                widget = self._create_widget_for_field(field)
                self._field_widgets[field.key] = widget
                form.addRow(field.label, widget)

            layout.addWidget(group)

        layout.addStretch()

    def _create_widget_for_field(self, field: FormatField) -> QWidget:
        """Create the appropriate widget for a formatting field."""
        if field.field_type == "color":
            button = ColorButton(field.default or "#FFFFFF", label=field.label)
            button.colorChanged.connect(self.values_changed.emit)
            return button

        elif field.field_type == "boolean":
            checkbox = QCheckBox()
            checkbox.setChecked(bool(field.default))
            checkbox.toggled.connect(self.values_changed.emit)
            return checkbox

        elif field.field_type == "number":
            spinbox = QSpinBox()
            spinbox.setMinimum(field.min_val or 0)
            spinbox.setMaximum(field.max_val or 100)
            if field.suffix:
                spinbox.setSuffix(f" {field.suffix}")
            spinbox.setValue(int(field.default or 0))
            spinbox.valueChanged.connect(self.values_changed.emit)
            return spinbox

        elif field.field_type == "dropdown":
            combo = QComboBox()
            if field.options:
                for value, label in field.options:
                    combo.addItem(label, value)
            combo.currentIndexChanged.connect(self.values_changed.emit)
            return combo

        else:
            # Default: text input (not implemented yet)
            raise NotImplementedError(f"Field type {field.field_type} not implemented")

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
        return values

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
