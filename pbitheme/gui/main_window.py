"""Main application window for the Power BI theme creator."""

from __future__ import annotations

import os
from typing import Dict

from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from ..model import PowerBITheme
from .widgets import (
    ColorButton,
    DataColorsEditor,
    TextClassEditor,
    VisualStyleEditor,
)


class MainWindow(QMainWindow):
    """Edit a :class:`PowerBITheme` on the left, preview its JSON on the right."""

    def __init__(self, theme: PowerBITheme | None = None) -> None:
        super().__init__()
        self._theme = theme or PowerBITheme()
        self._current_path: str | None = None
        self._structural_buttons: Dict[str, ColorButton] = {}
        self._text_editors: Dict[str, TextClassEditor] = {}

        self.setWindowTitle("Power BI Theme Creator")
        self.resize(1000, 720)

        self._build_menu()
        self._build_ui()
        self._load_from_theme(self._theme)
        self._refresh_preview()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new)

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open)

        save_action = QAction("&Save As...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        for action in (new_action, open_action, save_action):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Horizontal)

        # -- Left: editor form inside a scroll area ---------------------- #
        form_host = QWidget()
        form = QVBoxLayout(form_host)

        # General
        general_box = QGroupBox("General")
        general_layout = QFormLayout(general_box)
        self._name_edit = QLineEdit()
        self._name_edit.textChanged.connect(self._refresh_preview)
        general_layout.addRow("Theme name", self._name_edit)
        form.addWidget(general_box)

        # Structural colours
        struct_box = QGroupBox("Structural colours")
        struct_layout = QFormLayout(struct_box)
        for attr, _key, label, default in PowerBITheme.STRUCTURAL_FIELDS:
            button = ColorButton(default)
            button.colorChanged.connect(lambda _c: self._refresh_preview())
            self._structural_buttons[attr] = button
            struct_layout.addRow(label, button)
        form.addWidget(struct_box)

        # Data colours
        data_box = QGroupBox("Data colours")
        data_layout = QVBoxLayout(data_box)
        self._data_editor = DataColorsEditor(self._theme.data_colors)
        self._data_editor.changed.connect(self._refresh_preview)
        data_layout.addWidget(self._data_editor)
        form.addWidget(data_box)

        # Text classes
        text_box = QGroupBox("Text classes")
        text_layout = QFormLayout(text_box)
        for name, tc in self._theme.text_classes.items():
            editor = TextClassEditor(tc)
            editor.changed.connect(self._refresh_preview)
            self._text_editors[name] = editor
            text_layout.addRow(name.capitalize(), editor)
        form.addWidget(text_box)

        # Visual styles (detailed per-visual formatting -> visualStyles)
        visual_box = QGroupBox("Visual styles")
        visual_layout = QVBoxLayout(visual_box)
        visual_layout.addWidget(
            QLabel(
                "Enable a card to include it in visualStyles. Add tabs to target "
                "specific visuals; \"All visuals (*)\" applies to everything."
            )
        )
        self._visual_editor = VisualStyleEditor(self._theme.visual_styles)
        self._visual_editor.changed.connect(self._refresh_preview)
        visual_layout.addWidget(self._visual_editor)
        form.addWidget(visual_box)

        form.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_host)
        splitter.addWidget(scroll)

        # -- Right: JSON preview ---------------------------------------- #
        preview_host = QWidget()
        preview_layout = QVBoxLayout(preview_host)
        preview_layout.addWidget(QLabel("JSON preview"))
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFont(QFont("monospace", 10))
        preview_layout.addWidget(self._preview)
        splitter.addWidget(preview_host)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        container = QWidget()
        outer = QHBoxLayout(container)
        outer.addWidget(splitter)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------ #
    # Model <-> widgets
    # ------------------------------------------------------------------ #
    def _load_from_theme(self, theme: PowerBITheme) -> None:
        """Push *theme* values into the widgets (used by New / Open)."""
        self._name_edit.setText(theme.name)
        for attr, button in self._structural_buttons.items():
            button.set_color(getattr(theme, attr))
        self._data_editor.set_colors(theme.data_colors)
        for name, editor in self._text_editors.items():
            if name in theme.text_classes:
                tc = theme.text_classes[name]
                editor._font.setCurrentText(tc.font_face)
                editor._size.setValue(tc.font_size)
                editor._color.set_color(tc.color)
        self._visual_editor.set_styles(theme.visual_styles)

    def _collect_theme(self) -> PowerBITheme:
        """Build a fresh :class:`PowerBITheme` from the current widget state."""
        theme = PowerBITheme(name=self._name_edit.text().strip() or "My Theme")
        for attr, button in self._structural_buttons.items():
            setattr(theme, attr, button.color())
        theme.data_colors = self._data_editor.colors()
        theme.text_classes = {
            name: editor.value() for name, editor in self._text_editors.items()
        }
        theme.visual_styles = self._visual_editor.styles()
        return theme

    def _refresh_preview(self) -> None:
        self._theme = self._collect_theme()
        self._preview.setPlainText(self._theme.to_json())

    # ------------------------------------------------------------------ #
    # Menu actions
    # ------------------------------------------------------------------ #
    def _on_new(self) -> None:
        self._current_path = None
        self._load_from_theme(PowerBITheme())
        self._refresh_preview()
        self.statusBar().showMessage("New theme")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open theme", "", "JSON files (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            theme = PowerBITheme.load(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Open failed", f"Could not load theme:\n{exc}")
            return
        self._current_path = path
        self._load_from_theme(theme)
        self._refresh_preview()
        self.statusBar().showMessage(f"Opened {os.path.basename(path)}")

    def _on_save(self) -> None:
        theme = self._collect_theme()
        default_name = (theme.name or "theme").replace(" ", "_") + ".json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save theme", default_name, "JSON files (*.json);;All files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            theme.save(path)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", f"Could not save theme:\n{exc}")
            return
        self._current_path = path
        self.statusBar().showMessage(f"Saved {os.path.basename(path)}")
