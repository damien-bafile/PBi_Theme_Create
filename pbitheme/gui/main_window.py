"""Main application window for the Power BI theme creator."""

from __future__ import annotations

import copy
import os
from typing import Any, Dict

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
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
from PySide6.QtCore import Qt, QThread, Signal

from ..model import PowerBITheme, VISUAL_TYPES
from ..pbix_import import extract_theme_from_pbix, NoThemeFoundError
from ..screenshot import capture_widget
from .widgets import (
    ColorButton, DataColorsEditor, TextClassEditor, VisualStylesChecklist, InlineBanner,
)
from .visual_style_dialog import VisualStyleDialog
from .preview_panel import PreviewPanel
from . import theme
from .history import ThemeHistory


# Plain-language hints for the Power BI structural colour classes (P3: jargon).
_STRUCTURAL_TIPS = {
    "foreground": "Default text and label colour on visuals.",
    "second_level": "Secondary / muted text (axis labels, subtitles).",
    "third_level": "Gridlines and grid backgrounds.",
    "fourth_level": "Dimmed elements and inactive category text.",
    "background": "Visual and page background.",
    "secondary_background": "Secondary surfaces (e.g. slicer panes, headers).",
    "table_accent": "Accent colour for table/matrix headers and highlights.",
    "good": "Positive / on-target sentiment (KPIs, conditional formatting).",
    "neutral": "Neutral sentiment.",
    "bad": "Negative / off-target sentiment.",
    "gradient_min": "Low end of conditional-formatting colour scales.",
    "gradient_center": "Midpoint of diverging colour scales.",
    "gradient_max": "High end of conditional-formatting colour scales.",
    "gradient_null": "Colour used for blank / N/A values.",
}


class _SchemaCheckWorker(QThread):
    """Fetch the latest upstream schema version off the UI thread."""

    done = Signal(dict)

    def run(self) -> None:  # noqa: D401 - Qt override
        from ..schema_update import check_for_update

        try:
            self.done.emit(check_for_update())
        except Exception as exc:  # pragma: no cover - check_for_update shouldn't raise
            self.done.emit(
                {"bundled": None, "latest": None, "update_available": False, "error": str(exc)}
            )


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
        self._schema_worker: _SchemaCheckWorker | None = None
        self._skip_history_record = False  # Flag to prevent recording during undo/redo
        self._dirty = False
        self._loading = False  # suppress dirty-marking while pushing a theme into widgets
        self._committed: PowerBITheme | None = None  # last committed snapshot (undo baseline)

        self.setWindowTitle("Power BI Theme Creator")
        self.resize(1000, 720)

        self._build_menu()
        self._build_ui()
        self._loading = True
        self._load_from_theme(self._theme)
        self._refresh_preview()
        self._loading = False
        self._committed = self._collect_theme()
        self._set_dirty(False)

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

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._on_save_as)

        screenshot_action = QAction("Save &Screenshot...", self)
        screenshot_action.triggered.connect(self._on_save_screenshot)

        validate_action = QAction("&Validate against Power BI schema", self)
        validate_action.setShortcut("Ctrl+L")
        validate_action.triggered.connect(self._on_validate)

        self._update_action = QAction("Check for Schema &Update...", self)
        self._update_action.triggered.connect(self._on_check_schema_update)

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        for action in (new_action, open_action, save_action, save_as_action, screenshot_action):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(validate_action)
        file_menu.addAction(self._update_action)
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
        self._redo_action.setShortcuts(["Ctrl+Y", "Ctrl+Shift+Z"])
        self._redo_action.triggered.connect(self._on_redo)
        self._redo_action.setEnabled(False)
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()

        from PySide6.QtCore import QSettings
        self._dark_action = QAction("&Dark Mode", self)
        self._dark_action.setCheckable(True)
        self._dark_action.setChecked(bool(QSettings().value("ui/darkMode", False, type=bool)))
        self._dark_action.toggled.connect(self._on_toggle_dark)
        edit_menu.addAction(self._dark_action)

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
        # Commit one undo step per name edit (on focus-out / Enter, not per keystroke).
        self._name_edit.editingFinished.connect(self._record_history)
        general_layout.addRow("Theme name", self._name_edit)
        form.addWidget(general_box)

        # Structural colours
        struct_box = QGroupBox("Structural colours")
        struct_layout = QFormLayout(struct_box)
        for attr, _key, label, default in PowerBITheme.STRUCTURAL_FIELDS:
            button = ColorButton(default, label=label)
            button.colorChanged.connect(lambda _c: self._refresh_preview())
            button.colorChanged.connect(lambda _c: self._record_history())
            tip = _STRUCTURAL_TIPS.get(attr)
            if tip:
                button.setToolTip(tip)
            self._structural_buttons[attr] = button
            struct_layout.addRow(label, button)
        form.addWidget(struct_box)

        # Conditional-formatting gradient colours
        gradient_box = QGroupBox("Conditional formatting colours")
        gradient_layout = QFormLayout(gradient_box)
        for attr, _key, label, default in PowerBITheme.GRADIENT_FIELDS:
            button = ColorButton(default, label=label)
            button.colorChanged.connect(lambda _c: self._refresh_preview())
            button.colorChanged.connect(lambda _c: self._record_history())
            tip = _STRUCTURAL_TIPS.get(attr)
            if tip:
                button.setToolTip(tip)
            self._structural_buttons[attr] = button
            gradient_layout.addRow(label, button)
        form.addWidget(gradient_box)

        # Data colours
        data_box = QGroupBox("Data colours")
        data_layout = QVBoxLayout(data_box)
        self._data_editor = DataColorsEditor(self._theme.data_colors)
        self._data_editor.changed.connect(self._refresh_preview)
        self._data_editor.changed.connect(self._record_history)
        data_layout.addWidget(self._data_editor)
        form.addWidget(data_box)

        # Text classes
        text_box = QGroupBox("Text classes")
        text_layout = QFormLayout(text_box)
        for name, tc in self._theme.text_classes.items():
            editor = TextClassEditor(tc)
            editor.changed.connect(self._refresh_preview)
            editor.changed.connect(self._record_history)
            self._text_editors[name] = editor
            text_layout.addRow(name.capitalize(), editor)
        form.addWidget(text_box)

        # Visual styles — the product's headline capability, so surface it near
        # the top of the form (right after General) instead of below every colour
        # and text section where it fell off the initial fold.
        visual_box = QGroupBox("Visual styles")
        visual_layout = QVBoxLayout(visual_box)
        self._visual_checklist = VisualStylesChecklist()
        self._visual_checklist.visualRequested.connect(self._on_edit_visual_style)
        visual_layout.addWidget(self._visual_checklist)
        # Empty state: guide the user until at least one visual is customized.
        self._visual_hint = QLabel(
            "No visuals customized yet — click any visual above to style it."
        )
        self._visual_hint.setWordWrap(True)
        self._visual_hint.setStyleSheet("color: #605E5C; font-style: italic; padding: 2px;")
        visual_layout.addWidget(self._visual_hint)
        form.insertWidget(1, visual_box)

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
        self._preview.setFont(theme.monospace_font(10))
        json_layout.addWidget(self._preview)
        preview_tabs.addTab(json_host, "JSON Preview")

        splitter.addWidget(preview_tabs)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._build_welcome_banner())
        outer.addWidget(self._build_schema_banner())
        outer.addWidget(splitter, 1)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Ready")

        # Set up keyboard navigation (tab order)
        self._setup_tab_order()

    def _build_welcome_banner(self) -> QWidget:
        """A dismissible first-run banner that explains the basic workflow.

        Shown only until the user dismisses it (persisted via QSettings), so it
        onboards newcomers without nagging returning users.
        """
        from PySide6.QtCore import QSettings

        banner = InlineBanner()
        self._welcome_banner = banner
        banner.show_message(
            "<b>Welcome!</b> Set your palette and text on the left, click any "
            "<b>visual</b> to customize it, then <b>File → Save</b> to export a "
            "Power BI theme. The right panel previews every change live.",
            "info",
        )

        def _dismiss() -> None:
            QSettings().setValue("ui/welcomeDismissed", True)
            banner.hide()

        banner.add_button("Got it", _dismiss, "Don't show this again")

        try:
            dismissed = QSettings().value("ui/welcomeDismissed", False, type=bool)
        except Exception:
            dismissed = False
        banner.setVisible(not dismissed)
        return banner

    def _build_schema_banner(self) -> QWidget:
        """A hidden-until-needed banner that reports schema-update results inline."""
        banner = InlineBanner()
        self._schema_banner = banner
        banner.add_button("✕", banner.hide, "Dismiss")
        banner.hide()
        return banner

    def _restyle_banners(self) -> None:
        """Re-colour the inline banners for the active light/dark mode."""
        for attr in ("_welcome_banner", "_schema_banner"):
            banner = getattr(self, attr, None)
            if banner is not None:
                banner.restyle()

    def _on_toggle_dark(self, checked: bool) -> None:
        """Switch between the light and dark palette and remember the choice."""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QSettings

        theme.apply_palette(QApplication.instance(), checked)
        QSettings().setValue("ui/darkMode", checked)
        self._restyle_banners()  # banners use hardcoded hex, so re-theme them too
        # Re-colour the ✓/✗ status labels for the new mode (they're mode-aware).
        self._refresh_preview()

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
        if hasattr(self, "_visual_hint"):
            self._visual_hint.setVisible(not any(self._visual_styles.values()))
        self._update_history_actions()
        if not self._loading:
            self._set_dirty(True)
        self._update_title()

    # ------------------------------------------------------------------ #
    # Dirty state / window title
    # ------------------------------------------------------------------ #
    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        self.setWindowModified(dirty)

    def _update_title(self) -> None:
        """Show the current file (or theme name) plus an unsaved-changes marker."""
        if self._current_path:
            base = os.path.basename(self._current_path)
        else:
            base = (self._name_edit.text().strip() or "Untitled")
        # `[*]` is Qt's placeholder for the modified marker (driven by setWindowModified).
        self.setWindowTitle(f"{base}[*] — Power BI Theme Creator")

    def _confirm_discard(self) -> bool:
        """Return True if it's safe to throw away the current theme."""
        if not self._dirty:
            return True
        resp = QMessageBox.question(
            self, "Discard changes?",
            "This theme has unsaved changes. Discard them?",
            QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel,
        )
        return resp == QMessageBox.Discard

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    def _record_history(self) -> None:
        """Commit an edit: push the pre-edit baseline for undo, then rebase.

        Recording the *previous* committed state (not the current one) is what
        makes Ctrl+Z actually step back one edit. Skipped during load and during
        undo/redo playback.
        """
        if self._skip_history_record or self._loading:
            return
        if self._committed is not None:
            self._history.push(self._committed)
        self._committed = self._collect_theme()
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
        if not self._confirm_discard():
            return
        self._current_path = None
        self._visual_styles = {}
        self._history.clear()
        self._loading = True
        self._load_from_theme(PowerBITheme())
        self._refresh_preview()
        self._loading = False
        self._committed = self._collect_theme()
        self._set_dirty(False)
        self._update_title()
        self.statusBar().showMessage("New theme")

    def _on_open(self) -> None:
        if not self._confirm_discard():
            return
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
            QMessageBox.critical(
                self, "Open failed",
                f"Could not open {os.path.basename(path)}:\n{exc}\n\n"
                f"Make sure it's a valid Power BI theme (.json) or report "
                f"(.pbix / .pbit) file.",
            )
            self.statusBar().showMessage("Ready")
            return

        self._current_path = path
        self._history.clear()
        self._loading = True
        self._load_from_theme(theme)
        self._refresh_preview()
        self._loading = False
        self._committed = self._collect_theme()
        self._set_dirty(False)
        self._update_title()
        self.statusBar().showMessage(f"Opened {os.path.basename(path)}")

    def _on_save(self) -> None:
        """Save to the current file, or fall back to Save As when there is none."""
        if not self._current_path:
            self._on_save_as()
            return
        self._write_theme(self._current_path)

    def _on_save_as(self) -> None:
        theme = self._collect_theme()
        default_name = (theme.name or "theme").replace(" ", "_") + ".json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save theme", default_name, "JSON files (*.json);;All files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        self._write_theme(path)

    def _write_theme(self, path: str) -> None:
        theme = self._collect_theme()
        self.statusBar().showMessage(f"Saving {os.path.basename(path)}...")
        try:
            theme.save(path)
        except OSError as exc:
            QMessageBox.critical(
                self, "Save failed",
                f"Could not save to {os.path.basename(path)}:\n{exc}\n\n"
                f"Check the folder exists and is writable, then try again.",
            )
            self.statusBar().showMessage("Ready")
            return
        self._current_path = path
        self._set_dirty(False)
        self._update_title()
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

    def _on_check_schema_update(self) -> None:
        """Check upstream (off the UI thread) for a newer Power BI schema."""
        if self._schema_worker is not None:
            return  # a check is already running
        self._update_action.setEnabled(False)
        self.statusBar().showMessage("Checking for schema updates…")
        self._schema_worker = _SchemaCheckWorker(self)
        self._schema_worker.done.connect(self._on_schema_check_done)
        self._schema_worker.start()

    def _on_schema_check_done(self, info: Dict[str, Any]) -> None:
        self._update_action.setEnabled(True)
        worker, self._schema_worker = self._schema_worker, None
        if worker is not None:
            worker.deleteLater()

        bundled = info.get("bundled") or "unknown"
        if info.get("error"):
            self._schema_banner.show_message(
                "<b>Couldn't check for schema updates.</b> "
                f"Could not reach the source ({info['error']}). "
                "Check your connection and try again.",
                "warning",
            )
            self.statusBar().showMessage("Schema update check failed")
        elif info.get("update_available"):
            latest = info.get("latest")
            self._schema_banner.show_message(
                "<b>Schema update available.</b> A newer Power BI report theme "
                f"schema is out (bundled <b>v{bundled}</b>, latest <b>v{latest}</b>). "
                "It'll be included in a future release.",
                "info",
            )
            self.statusBar().showMessage(f"Schema update available: v{latest}")
        else:
            self._schema_banner.show_message(
                f"<b>Schema up to date.</b> You have the latest Power BI report "
                f"theme schema (<b>v{bundled}</b>).",
                "success",
            )
            self.statusBar().showMessage(f"Schema up to date (v{bundled})")

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

    def _apply_history_state(self, theme: PowerBITheme) -> None:
        """Load a theme from history without recording it as a new edit."""
        self._committed = copy.deepcopy(theme)
        self._skip_history_record = True
        self._loading = True
        self._load_from_theme(theme)
        self._refresh_preview()
        self._loading = False
        self._skip_history_record = False
        self._set_dirty(True)
        self._update_title()
        self._update_history_actions()

    def _on_undo(self) -> None:
        """Undo the last theme change (restore the previous committed state)."""
        if not self._history.can_undo():
            return
        # Current committed state becomes available for redo.
        self._history.save_for_redo(self._committed if self._committed is not None else self._collect_theme())
        prev_theme = self._history.undo()
        if prev_theme is not None:
            self._apply_history_state(prev_theme)
            self.statusBar().showMessage("Undo")

    def _on_redo(self) -> None:
        """Redo the last undone change."""
        if not self._history.can_redo():
            return
        # Keep the current state on the undo stack (without clearing redo).
        self._history.append_undo(self._committed if self._committed is not None else self._collect_theme())
        next_theme = self._history.redo()
        if next_theme is not None:
            self._apply_history_state(next_theme)
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
