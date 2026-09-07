"""Main application window for the Power BI theme creator."""

from __future__ import annotations

import copy
import os
from typing import Any, Dict

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
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QDialog,
)
from PySide6.QtCore import Qt

from ..model import PowerBITheme, VISUAL_TYPES
from ..pbix_import import extract_theme_from_pbix, NoThemeFoundError
from ..screenshot import capture_widget
from .widgets import ColorButton, DataColorsEditor, TextClassEditor, VisualStylesChecklist
from .visual_style_dialog import VisualStyleDialog
from .preview_panel import PreviewPanel
from .history import ThemeHistory


class MainWindow(QMainWindow):
    """Edit a :class:`PowerBITheme` on the left, preview its JSON on the right."""

    def __init__(self, theme: PowerBITheme | None = None) -> None:
        super().__init__()
        self._theme = theme or PowerBITheme()
        self._current_path: str | None = None
        self._structural_buttons: Dict[str, ColorButton] = {}
        self._text_editors: Dict[str, TextClassEditor] = {}
        self._visual_styles: Dict[str, Dict[str, Any]] = {}
        self._history = ThemeHistory(max_size=20)
        self._undo_action: QAction | None = None
        self._redo_action: QAction | None = None
        self._skip_history_record = False  # Flag to prevent recording during undo/redo

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
        # File menu
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

        screenshot_action = QAction("Save &Screenshot...", self)
        screenshot_action.triggered.connect(self._on_save_screenshot)

        validate_action = QAction("&Validate against Power BI schema", self)
        validate_action.setShortcut("Ctrl+L")
        validate_action.triggered.connect(self._on_validate)

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        for action in (new_action, open_action, save_action, screenshot_action):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(validate_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        # Edit menu with undo/redo
        edit_menu = self.menuBar().addMenu("&Edit")

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut("Ctrl+Z")
        self._undo_action.triggered.connect(self._on_undo)
        self._undo_action.setEnabled(False)
        edit_menu.addAction(self._undo_action)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut("Ctrl+Y")
        self._redo_action.triggered.connect(self._on_redo)
        self._redo_action.setEnabled(False)
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()

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
            button = ColorButton(default, label=label)
            button.colorChanged.connect(lambda _c: self._refresh_preview())
            self._structural_buttons[attr] = button
            struct_layout.addRow(label, button)
        form.addWidget(struct_box)

        # Conditional-formatting gradient colours
        gradient_box = QGroupBox("Conditional formatting colours")
        gradient_layout = QFormLayout(gradient_box)
        for attr, _key, label, default in PowerBITheme.GRADIENT_FIELDS:
            button = ColorButton(default, label=label)
            button.colorChanged.connect(lambda _c: self._refresh_preview())
            self._structural_buttons[attr] = button
            gradient_layout.addRow(label, button)
        form.addWidget(gradient_box)

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

        # Visual styles
        visual_box = QGroupBox("Visual styles")
        visual_layout = QVBoxLayout(visual_box)
        self._visual_checklist = VisualStylesChecklist()
        self._visual_checklist.visualRequested.connect(self._on_edit_visual_style)
        visual_layout.addWidget(self._visual_checklist)
        form.addWidget(visual_box)

        form.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_host)
        splitter.addWidget(scroll)

        # -- Right: Preview tabs (Visual + JSON) ---------------------- #
        preview_tabs = QTabWidget()

        # Visual preview tab
        self._visual_preview = PreviewPanel(self._theme)
        preview_tabs.addTab(self._visual_preview, "Visual Preview")

        # JSON preview tab
        json_host = QWidget()
        json_layout = QVBoxLayout(json_host)
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFont(QFont("monospace", 10))
        json_layout.addWidget(self._preview)
        preview_tabs.addTab(json_host, "JSON Preview")

        splitter.addWidget(preview_tabs)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        container = QWidget()
        outer = QHBoxLayout(container)
        outer.addWidget(splitter)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Ready")

        # Set up keyboard navigation (tab order)
        self._setup_tab_order()

    def _setup_tab_order(self) -> None:
        """Define keyboard tab order for accessibility."""
        # Start with theme name, then structural colors, then data colors, then text, then visuals
        current_widget = self._name_edit
        for button in self._structural_buttons.values():
            QWidget.setTabOrder(current_widget, button)
            current_widget = button
        QWidget.setTabOrder(current_widget, self._data_editor)
        current_widget = self._data_editor
        for editor in self._text_editors.values():
            QWidget.setTabOrder(current_widget, editor)
            current_widget = editor
        QWidget.setTabOrder(current_widget, self._visual_checklist)

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
        self._visual_styles = copy.deepcopy(theme.visual_styles)

    def _collect_theme(self) -> PowerBITheme:
        """Build a fresh :class:`PowerBITheme` from the current widget state."""
        theme = PowerBITheme(name=self._name_edit.text().strip() or "My Theme")
        for attr, button in self._structural_buttons.items():
            setattr(theme, attr, button.color())
        theme.data_colors = self._data_editor.colors()
        theme.text_classes = {
            name: editor.value() for name, editor in self._text_editors.items()
        }
        theme.visual_styles = copy.deepcopy(self._visual_styles)
        return theme

    def _refresh_preview(self) -> None:
        self._theme = self._collect_theme()
        self._preview.setPlainText(self._theme.to_json())
        self._visual_checklist.set_theme(self._theme)
        self._visual_preview.update_preview(self._theme, self._visual_styles)
        self._update_history_actions()

    def _record_history(self) -> None:
        """Record current theme state for undo (unless skipped during undo/redo)."""
        if self._skip_history_record:
            return
        self._history.push(self._collect_theme())
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        """Update undo/redo menu items based on history availability."""
        if self._undo_action:
            self._undo_action.setEnabled(self._history.can_undo())
        if self._redo_action:
            self._redo_action.setEnabled(self._history.can_redo())

    # ------------------------------------------------------------------ #
    # Menu actions
    # ------------------------------------------------------------------ #
    def _on_new(self) -> None:
        self._current_path = None
        self._visual_styles = {}
        self._history.clear()
        self._load_from_theme(PowerBITheme())
        self._refresh_preview()
        self.statusBar().showMessage("New theme")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open theme or Power BI file", "",
            "Power BI files (*.pbix *.pbit *.json);;All files (*)"
        )
        if not path:
            return

        self.statusBar().showMessage(f"Opening {os.path.basename(path)}...")
        try:
            if path.lower().endswith((".pbix", ".pbit")):
                theme = extract_theme_from_pbix(path)
            else:
                theme = PowerBITheme.load(path)
        except NoThemeFoundError as exc:
            QMessageBox.warning(self, "No custom theme", str(exc))
            self.statusBar().showMessage("Ready")
            return
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Open failed", f"Could not load theme:\n{exc}")
            self.statusBar().showMessage("Ready")
            return

        self._current_path = path
        self._history.clear()
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
        self.statusBar().showMessage(f"Saving {os.path.basename(path)}...")
        try:
            theme.save(path)
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", f"Could not save theme:\n{exc}")
            self.statusBar().showMessage("Ready")
            return
        self._current_path = path
        self.statusBar().showMessage(f"Saved {os.path.basename(path)}")

    def _on_validate(self) -> None:
        """Validate the current theme against the bundled Power BI schema."""
        from ..validate import schema_version, validate_theme

        theme = self._collect_theme()
        try:
            errors = validate_theme(theme.to_dict())
        except RuntimeError as exc:
            QMessageBox.warning(self, "Validation unavailable", str(exc))
            return

        version = schema_version() or "unknown"
        if not errors:
            QMessageBox.information(
                self,
                "Valid",
                f"The theme conforms to the Power BI report theme schema "
                f"(v{version}).",
            )
            self.statusBar().showMessage(f"Valid against schema v{version}")
            return

        preview = "\n".join(f"• {e}" for e in errors[:20])
        if len(errors) > 20:
            preview += f"\n... and {len(errors) - 20} more."
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Schema issues")
        box.setText(f"{len(errors)} issue(s) found against schema v{version}.")
        box.setDetailedText(preview)
        box.exec()
        self.statusBar().showMessage(f"{len(errors)} schema issue(s)")

    def _on_edit_visual_style(self, visual_key: str) -> None:
        """Open the style editor dialog for the selected visual type."""
        label = dict(VISUAL_TYPES).get(visual_key, visual_key)
        presets = self._visual_styles.get(visual_key) or {}
        existing_obj = presets.get("*", {})
        dialog = VisualStyleDialog(
            visual_key, label, existing_obj, self, self._theme, presets=presets or None
        )
        if dialog.exec() == QDialog.Accepted:
            # Keep the default plus any non-empty named presets.
            updated = {
                name: obj for name, obj in dialog.result_presets().items()
                if obj or name == "*"
            }
            has_content = any(obj for obj in updated.values())
            if has_content:
                self._visual_styles[visual_key] = updated
            else:
                self._visual_styles.pop(visual_key, None)
            self._record_history()
            self._refresh_preview()

    def _on_undo(self) -> None:
        """Undo the last theme change."""
        if not self._history.can_undo():
            return
        # Save current state for redo
        self._history.save_for_redo(self._theme)
        # Get previous state
        prev_theme = self._history.undo()
        if prev_theme:
            self._skip_history_record = True
            self._load_from_theme(prev_theme)
            self._refresh_preview()
            self._skip_history_record = False
            self.statusBar().showMessage("Undo")

    def _on_redo(self) -> None:
        """Redo the last undone change."""
        if not self._history.can_redo():
            return
        # Get next state
        next_theme = self._history.redo()
        if next_theme:
            self._skip_history_record = True
            self._load_from_theme(next_theme)
            self._refresh_preview()
            self._skip_history_record = False
            self.statusBar().showMessage("Redo")

    def _on_save_screenshot(self) -> None:
        """Save a PNG screenshot of the current window."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save screenshot", "theme_editor.png", "PNG images (*.png);;All files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        self.statusBar().showMessage(f"Saving screenshot {os.path.basename(path)}...")
        try:
            capture_widget(self, path)
        except OSError as exc:
            QMessageBox.critical(self, "Screenshot failed", f"Could not save screenshot:\n{exc}")
            self.statusBar().showMessage("Ready")
            return
        self.statusBar().showMessage(f"Saved screenshot {os.path.basename(path)}")
