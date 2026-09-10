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
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFontComboBox,
    QGridLayout,
    QScrollArea,
    QCheckBox,
    QComboBox,
    QPlainTextEdit,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QDialogButtonBox,
    QDialog,
    QFrame,
)

from ..model import (
    PowerBITheme, TextClass, VISUAL_TYPES, LEGEND_POSITIONS,
    is_valid_hex, normalise_hex,
    build_background_object, build_border_object, build_title_object,
    build_data_labels_object, build_legend_object,
    unpack_background_object, unpack_border_object, unpack_title_object,
    unpack_data_labels_object, unpack_legend_object,
    merge_visual_style_entry
)
from . import theme


def _wcag_luminance(c: QColor) -> float:
    """WCAG 2.x relative luminance of a colour (0=black … 1=white)."""
    def _lin(v: float) -> float:
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(c.red()) + 0.7152 * _lin(c.green()) + 0.0722 * _lin(c.blue())


def _readable_text_color(hex_color: str) -> str:
    """Return black or white — whichever has the higher WCAG contrast on *hex_color*."""
    lum = _wcag_luminance(QColor(hex_color))
    contrast_white = (1.0 + 0.05) / (lum + 0.05)
    contrast_black = (lum + 0.05) / 0.05
    return theme.SURFACE_BACKGROUND if contrast_white >= contrast_black else theme.TEXT_STRONG


# Per-variant banner colours: (light bg, light border, dark bg, dark border).
_BANNER_VARIANTS = {
    "info":    ("#EFF6FF", "#BBD6FF", "#14304A", "#2A4A6A"),
    "success": ("#ECFDF3", "#A6E9C5", "#10312A", "#1E5E4A"),
    "warning": ("#FEF3E7", "#F5C48A", "#3A2A12", "#6A4A1E"),
}


class InlineBanner(QFrame):
    """A dismissible, mode-aware inline notification strip.

    One reusable widget for both the first-run welcome message and transient
    status notices (e.g. the schema-update result), so they share look and
    theming instead of duplicating stylesheet logic. Call :meth:`restyle` when
    the light/dark palette changes.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._variant = "info"
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 6, 6, 6)
        row.setSpacing(6)
        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self._label.setOpenExternalLinks(True)
        row.addWidget(self._label, 1)
        self._button_row = QHBoxLayout()
        self._button_row.setContentsMargins(0, 0, 0, 0)
        self._button_row.setSpacing(6)
        row.addLayout(self._button_row, 0)

    def add_button(self, text: str, on_click, tooltip: str = "") -> QPushButton:
        """Append a trailing button (e.g. 'Got it' or a close '✕')."""
        btn = QPushButton(text)
        if tooltip:
            btn.setToolTip(tooltip)
        btn.clicked.connect(on_click)
        self._button_row.addWidget(btn)
        return btn

    def show_message(self, html: str, variant: str = "info") -> None:
        """Set the (rich-text) message, colour it by *variant*, and reveal."""
        self._label.setText(html)
        self._variant = variant if variant in _BANNER_VARIANTS else "info"
        self.restyle()
        self.show()

    def restyle(self) -> None:
        """Re-apply colours for the active light/dark mode and current variant."""
        light_bg, light_border, dark_bg, dark_border = _BANNER_VARIANTS[self._variant]
        if theme.dark_mode:
            bg, border, fg = dark_bg, dark_border, theme.DARK_TEXT
        else:
            bg, border, fg = light_bg, light_border, theme.TEXT_PRIMARY
        self.setStyleSheet(
            f"InlineBanner {{ background: {bg}; border: 1px solid {border}; border-radius: 4px; }}"
        )
        self._label.setStyleSheet(f"border: none; background: transparent; color: {fg};")


class ColorButton(QPushButton):
    """A button that shows a colour swatch and opens a colour picker."""

    colorChanged = Signal(str)

    def __init__(self, color: str = "#FFFFFF", label: str = "Color", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = normalise_hex(color) if is_valid_hex(color) else "#FFFFFF"
        self._label = label
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
        # Pick the text colour (black or white) with the higher WCAG contrast
        # against the swatch, so the hex stays readable on saturated fills.
        text = _readable_text_color(self._color)
        self.setText(self._color)
        self.setStyleSheet(
            f"background-color: {self._color}; color: {text};"
            f"border: 1px solid {theme.BORDER_SUBTLE}; border-radius: 4px;"
            f"font-family: {theme.MONOSPACE_STACK};"
        )
        # Set accessible name and description for screen readers
        self.setAccessibleName(f"{self._label} color button")
        self.setAccessibleDescription(f"Current color: {self._color}. Click to open color picker.")


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
        add_btn.clicked.connect(lambda: self.set_colors(self.colors() + ["#118DFF"]))
        controls.addWidget(add_btn)
        controls.addStretch(1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self._rows)
        outer.addLayout(controls)

        self.set_colors(colors)

    def colors(self) -> List[str]:
        return [btn.color() for btn in self._buttons]

    def set_colors(self, colors: List[str]) -> None:
        self._rebuild(list(colors))
        self.changed.emit()

    def _rebuild(self, colors: List[str]) -> None:
        """Recreate every row so per-row deletes stay correctly numbered."""
        while self._rows.count():
            item = self._rows.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._buttons = []
        for i, color in enumerate(colors):
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(QLabel(f"{i + 1}."))
            button = ColorButton(color, label=f"Data color {i + 1}")
            button.colorChanged.connect(lambda _c: self.changed.emit())
            self._buttons.append(button)
            layout.addWidget(button)
            del_btn = QPushButton("✕")
            del_btn.setFixedWidth(28)
            del_btn.setToolTip("Remove this colour")
            del_btn.setAccessibleName(f"Remove data color {i + 1}")
            del_btn.clicked.connect(lambda _=False, idx=i: self._remove_at(idx))
            layout.addWidget(del_btn)
            layout.addStretch(1)
            self._rows.addWidget(row)

    def _remove_at(self, idx: int) -> None:
        cols = self.colors()
        if 0 <= idx < len(cols):
            del cols[idx]
            self.set_colors(cols)


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
        self._font.setAccessibleName(f"{text_class.name} font")
        self._font.setAccessibleDescription("Select font family")

        self._size = QSpinBox()
        self._size.setRange(4, 120)
        self._size.setValue(text_class.font_size)
        self._size.setSuffix(" pt")
        self._size.valueChanged.connect(lambda _v: self.changed.emit())
        self._size.setAccessibleName(f"{text_class.name} size")
        self._size.setAccessibleDescription("Font size in points")

        self._color = ColorButton(text_class.color, label=f"{text_class.name} color")
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
    """Scrollable checklist of Power BI visual types with customization status. Rows are clickable."""

    visualRequested = Signal(str)

    @staticmethod
    def _name_style() -> str:
        # Explicit mode-aware colour (a bare QSS rule otherwise drops the palette
        # text colour and renders dim on the dark theme). Rows read as links.
        col = theme.DARK_TEXT if theme.dark_mode else theme.TEXT_PRIMARY
        return (
            f"QPushButton {{ text-align: left; border: none; padding: 2px; color: {col}; }}"
            "QPushButton:hover { text-decoration: underline; color: #118DFF; }"
        )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status_labels: dict[str, QLabel] = {}
        self._name_buttons: dict[str, QPushButton] = {}
        self._theme: PowerBITheme | None = None
        self._query = ""

        # Search / filter box so the 50+ visuals stay findable.
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter visuals…")
        self._search.setClearButtonEnabled(True)
        self._search.setAccessibleName("Filter visuals")
        self._search.textChanged.connect(self._on_filter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # One column so the status never gets pushed off-screen; the outer form
        # scrolls, and this inner list keeps a sensible height (~10 rows) rather
        # than collapsing to a cramped double-scrolled box.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Tall enough to not feel cramped, short enough that the colour sections
        # below still peek above the fold.
        scroll.setMinimumHeight(170)
        container = QWidget()
        self._grid = QGridLayout(container)
        self._grid.setColumnStretch(0, 1)   # visual name (stretches)
        self._grid.setColumnStretch(1, 0)   # status (fixed)
        self._grid.setSpacing(6)
        scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._search)
        layout.addWidget(scroll)

        self._populate()

    def _on_filter(self, text: str) -> None:
        self._query = text.strip().lower()
        self._populate()

    def _populate(self) -> None:
        """(Re)build the single-column list, showing only visuals matching the filter."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._status_labels = {}
        self._name_buttons = {}
        style = self._name_style()
        matches = [(k, l) for k, l in VISUAL_TYPES if self._query in l.lower()]
        for row, (key, label) in enumerate(matches):
            name_btn = QPushButton(label.replace("&", "&&"))  # && escapes the mnemonic
            name_btn.setFlat(True)
            name_btn.setCursor(Qt.PointingHandCursor)
            name_btn.setStyleSheet(style)
            self._name_buttons[key] = name_btn
            name_btn.clicked.connect(lambda _c=False, k=key: self.visualRequested.emit(k))
            status_label = QLabel("✗ Default")
            # Fixed width + right alignment so the status never truncates.
            status_label.setFixedWidth(90)
            status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._grid.addWidget(name_btn, row, 0)
            self._grid.addWidget(status_label, row, 1)
            self._status_labels[key] = status_label
        self._grid.setRowStretch(len(matches), 1)  # push rows to the top
        self._refresh_status()

    def _refresh_status(self) -> None:
        # "Custom" is the notable state — green + bold so it stands out; "Default"
        # is the quiet majority — a muted (still-AA) grey so 50+ rows aren't a wall.
        for key, label in self._status_labels.items():
            customised = self._theme is not None and self._theme.is_visual_customised(key)
            if customised:
                label.setText("✓ Custom")
                label.setStyleSheet(f"color: {theme.STATUS_CUSTOM_COLOR}; font-weight: bold;")
            else:
                label.setText("✗ Default")
                label.setStyleSheet(f"color: {theme.STATUS_MUTED_COLOR};")

    def set_theme(self, pbi_theme: PowerBITheme) -> None:
        """Update the checklist based on which visuals are customised."""
        self._theme = pbi_theme
        # Re-apply name colours so a light/dark toggle recolours existing rows.
        style = self._name_style()
        for btn in self._name_buttons.values():
            btn.setStyleSheet(style)
        self._refresh_status()
