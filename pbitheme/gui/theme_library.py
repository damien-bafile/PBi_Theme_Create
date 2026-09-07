"""Theme library panel for managing saved themes."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ..model import PowerBITheme


class ThemeLibrary(QWidget):
    """Sidebar widget for browsing and loading saved themes."""

    theme_selected = Signal(str)  # Emits path to selected theme file

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._folder: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Theme list
        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list)

        self.setAccessibleName("Theme Library")
        self.setAccessibleDescription("List of saved themes. Double-click to load.")

    def set_folder(self, folder: str | None) -> None:
        """Set the theme folder and refresh the list."""
        self._folder = folder
        self.refresh()

    def refresh(self) -> None:
        """Refresh the theme list from the current folder."""
        self._list.clear()

        if not self._folder or not os.path.isdir(self._folder):
            item = QListWidgetItem("No theme folder set. Use File menu to configure.")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self._list.addItem(item)
            return

        # Scan folder for .json files
        json_files = sorted(Path(self._folder).glob("*.json"))

        if not json_files:
            item = QListWidgetItem("No themes saved yet")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self._list.addItem(item)
            return

        for json_file in json_files:
            name = json_file.stem  # Filename without extension
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, str(json_file))  # Store full path
            self._list.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Load theme when double-clicked."""
        path = item.data(Qt.UserRole)
        if path:
            self.theme_selected.emit(path)

    def _on_context_menu(self, pos) -> None:
        """Show context menu for theme operations."""
        item = self._list.itemAt(pos)
        if not item or not item.data(Qt.UserRole):
            return

        path = item.data(Qt.UserRole)
        menu = QMenu()

        load_action = menu.addAction("Load")
        load_action.triggered.connect(lambda: self.theme_selected.emit(path))

        rename_action = menu.addAction("Rename...")
        rename_action.triggered.connect(lambda: self._rename_theme(path, item))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._delete_theme(path))

        export_action = menu.addAction("Export...")
        export_action.triggered.connect(lambda: self._export_theme(path))

        menu.exec(self._list.mapToGlobal(pos))

    def _rename_theme(self, path: str, item: QListWidgetItem) -> None:
        """Rename a theme file."""
        old_name = Path(path).stem
        new_name, ok = QInputDialog.getText(
            self, "Rename Theme", "New name:", text=old_name
        )
        if ok and new_name:
            new_path = str(Path(path).parent / f"{new_name}.json")
            try:
                os.rename(path, new_path)
                self.refresh()
            except OSError as e:
                QMessageBox.critical(self, "Rename failed", f"Could not rename theme:\n{e}")

    def _delete_theme(self, path: str) -> None:
        """Delete a theme file."""
        name = Path(path).stem
        reply = QMessageBox.question(
            self, "Delete Theme", f"Delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                os.remove(path)
                self.refresh()
            except OSError as e:
                QMessageBox.critical(self, "Delete failed", f"Could not delete theme:\n{e}")

    def _export_theme(self, path: str) -> None:
        """Export a theme to another location."""
        name = Path(path).stem
        export_path, _ = QFileDialog.getSaveFileName(
            self, "Export Theme", f"{name}.json", "JSON files (*.json)"
        )
        if export_path:
            try:
                with open(path, "r") as src, open(export_path, "w") as dst:
                    dst.write(src.read())
                QMessageBox.information(self, "Success", f"Theme exported to {os.path.basename(export_path)}")
            except OSError as e:
                QMessageBox.critical(self, "Export failed", f"Could not export theme:\n{e}")
