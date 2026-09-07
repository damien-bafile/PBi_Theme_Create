"""Reusable Qt widgets used by the theme editor.

Each widget is a self-contained class that exposes a ``changed`` signal so the
main window can rebuild the live JSON preview whenever anything is edited.
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFontComboBox,
)

from ..model import (
    VISUAL_TARGETS,
    CardSpec,
    PropSpec,
    TextClass,
    VisualStyle,
    cards_for,
    is_valid_hex,
    normalise_hex,
)


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
        self._extra = dict(text_class.extra)

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

    def set_value(self, text_class: TextClass) -> None:
        self._extra = dict(text_class.extra)
        self._font.setCurrentText(text_class.font_face)
        self._size.setValue(text_class.font_size)
        self._color.set_color(text_class.color)

    def value(self) -> TextClass:
        return TextClass(
            name=self._name,
            font_face=self._font.currentFont().family(),
            font_size=self._size.value(),
            color=self._color.color(),
            extra=dict(self._extra),
        )


class _PropWidget(QWidget):
    """A single labelled editor for one :class:`PropSpec` value."""

    changed = Signal()

    def __init__(self, spec: PropSpec, value, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._spec = spec
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._editor = self._build_editor(spec, value)
        layout.addWidget(self._editor)

    def _build_editor(self, spec: PropSpec, value):
        if spec.kind == "bool":
            w = QCheckBox()
            w.setChecked(bool(value))
            w.toggled.connect(lambda _v: self.changed.emit())
            return w
        if spec.kind == "color":
            w = ColorButton(value if is_valid_hex(value) else spec.default)
            w.colorChanged.connect(lambda _c: self.changed.emit())
            return w
        if spec.kind == "int":
            w = QSpinBox()
            w.setRange(-1000000, 1000000)
            w.setValue(int(value))
            w.valueChanged.connect(lambda _v: self.changed.emit())
            return w
        if spec.kind == "font":
            w = QFontComboBox()
            w.setCurrentText(str(value))
            w.currentFontChanged.connect(lambda _f: self.changed.emit())
            return w
        if spec.kind == "choice":
            w = QComboBox()
            for opt_value, opt_label in (spec.choices or []):
                w.addItem(opt_label, opt_value)
            idx = w.findData(value)
            w.setCurrentIndex(idx if idx >= 0 else 0)
            w.currentIndexChanged.connect(lambda _i: self.changed.emit())
            return w
        # fallback: read-only label
        return QLabel(str(value))

    def value(self):
        w = self._editor
        if self._spec.kind == "bool":
            return w.isChecked()
        if self._spec.kind == "color":
            return w.color()
        if self._spec.kind == "int":
            return w.value()
        if self._spec.kind == "font":
            return w.currentFont().family()
        if self._spec.kind == "choice":
            return w.currentData()
        return self._spec.default


class CardEditor(QGroupBox):
    """A checkable group box editing one formatting card of a visual."""

    changed = Signal()

    def __init__(self, spec: CardSpec, enabled: bool, values: dict,
                 parent: QWidget | None = None) -> None:
        super().__init__(spec.label, parent)
        self._card_key = spec.key
        self._prop_widgets = {}

        self.setCheckable(True)
        self.setChecked(bool(enabled))
        self.toggled.connect(lambda _v: self.changed.emit())

        form = QFormLayout(self)
        for prop in spec.props:
            widget = _PropWidget(prop, values.get(prop.key, prop.default))
            widget.changed.connect(self.changed.emit)
            self._prop_widgets[prop.key] = widget
            form.addRow(prop.label, widget)

    def card_key(self) -> str:
        return self._card_key

    def is_enabled(self) -> bool:
        return self.isChecked()

    def values(self) -> dict:
        return {key: w.value() for key, w in self._prop_widgets.items()}


class VisualTargetEditor(QWidget):
    """All formatting cards for a single visual target (e.g. "*" or "card")."""

    changed = Signal()

    def __init__(self, style: VisualStyle, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._visual = style.visual
        # Retain any unmodelled selectors/cards/properties for round-tripping.
        self._raw = style.raw
        self._cards = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        for card_key, spec in cards_for(style.visual).items():
            editor = CardEditor(spec, style.enabled.get(card_key, False),
                                style.values.get(card_key, {}))
            editor.changed.connect(self.changed.emit)
            self._cards[card_key] = editor
            layout.addWidget(editor)
        layout.addStretch(1)

    def visual(self) -> str:
        return self._visual

    def to_style(self) -> VisualStyle:
        style = VisualStyle(self._visual)
        style.raw = self._raw
        for card_key, editor in self._cards.items():
            style.enabled[card_key] = editor.is_enabled()
            style.values[card_key] = editor.values()
        return style


class VisualStyleEditor(QWidget):
    """Tabbed editor managing one :class:`VisualTargetEditor` per visual."""

    changed = Signal()

    def __init__(self, styles, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Add visual:"))
        self._picker = QComboBox()
        for visual, label in VISUAL_TARGETS.items():
            self._picker.addItem(label, visual)
        controls.addWidget(self._picker, 1)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_from_picker)
        controls.addWidget(add_btn)
        remove_btn = QPushButton("Remove current")
        remove_btn.clicked.connect(self._remove_current)
        controls.addWidget(remove_btn)

        self._tabs = QTabWidget()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(controls)
        outer.addWidget(self._tabs)

        self.set_styles(styles)

    # -- public API -------------------------------------------------------- #
    def set_styles(self, styles) -> None:
        self._tabs.clear()
        styles = list(styles) or [VisualStyle("*")]
        for style in styles:
            self._add_tab(style)
        self.changed.emit()

    def styles(self):
        return [self._tabs.widget(i).to_style() for i in range(self._tabs.count())]

    # -- helpers ----------------------------------------------------------- #
    def _add_tab(self, style: VisualStyle) -> None:
        editor = VisualTargetEditor(style)
        editor.changed.connect(self.changed.emit)
        label = VISUAL_TARGETS.get(style.visual, style.visual)
        self._tabs.addTab(editor, label)

    def _existing_visuals(self):
        return {self._tabs.widget(i).visual() for i in range(self._tabs.count())}

    def _add_from_picker(self) -> None:
        visual = self._picker.currentData()
        if visual in self._existing_visuals():
            # focus the existing tab instead of duplicating it
            for i in range(self._tabs.count()):
                if self._tabs.widget(i).visual() == visual:
                    self._tabs.setCurrentIndex(i)
                    return
        self._add_tab(VisualStyle(visual))
        self._tabs.setCurrentIndex(self._tabs.count() - 1)
        self.changed.emit()

    def _remove_current(self) -> None:
        if self._tabs.count() <= 1:
            return  # always keep at least one target
        self._tabs.removeTab(self._tabs.currentIndex())
        self.changed.emit()
