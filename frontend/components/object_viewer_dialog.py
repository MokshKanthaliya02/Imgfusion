# object_viewer_dialog.py

import os
import json
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QInputDialog,
    QMessageBox,
    QDialogButtonBox,
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

METADATA_PATH = r"D:/Projects/project1/data/object_metadata.json"

class ObjectViewerDialog(QDialog):
    image_renamed = pyqtSignal(str, str)

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.original_path = image_path
        self.rename_debounce_timer = QTimer(self)
        self.rename_debounce_timer.setSingleShot(True)
        self.rename_debounce_timer.timeout.connect(self._apply_metadata_update)

        self.setWindowTitle("Object Viewer")
        self.resize(900, 700)
        self._build_ui()
        self._load_image()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16,16,16,16)
        layout.setSpacing(8)

        # Scrollable image
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.image_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.image_label)
        layout.addWidget(self.scroll, 1)

        # Controls: zoom + rename
        ctr = QHBoxLayout()
        # Fit / Actual
        self.fit_btn = QPushButton("Fit to Window")
        self.fit_btn.setCheckable(True)
        self.fit_btn.clicked.connect(self._toggle_fit)
        ctr.addWidget(self.fit_btn)
        self.actual_btn = QPushButton("Actual Size")
        self.actual_btn.clicked.connect(lambda: self._toggle_fit(force=True))
        ctr.addWidget(self.actual_btn)
        # Rename
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setIcon(QIcon("frontend/assets/edit.svg"))
        self.rename_btn.clicked.connect(self._prompt_rename)
        ctr.addWidget(self.rename_btn)
        ctr.addStretch()
        layout.addLayout(ctr)

        # Filename display
        self.name_label = QLabel(os.path.basename(self.image_path), alignment=Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size:12px; color:#4B5563; padding:4px;")
        layout.addWidget(self.name_label)

        # Close button
        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_box.rejected.connect(self.reject)
        layout.addWidget(close_box)

    def _load_image(self):
        pix = QPixmap(self.image_path)
        self.image_label.setPixmap(pix)
        if self.fit_btn.isChecked():
            self._toggle_fit()

    def _toggle_fit(self, force=False):
        pix = QPixmap(self.image_path)
        if force or not self.fit_btn.isChecked():
            # actual size
            self.image_label.setPixmap(pix)
            self.fit_btn.setChecked(False)
            self.fit_btn.setText("Fit to Window")
        else:
            # fit
            scaled = pix.scaled(
                self.scroll.viewport().size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            self.fit_btn.setChecked(True)
            self.fit_btn.setText("Actual Size")

    def _prompt_rename(self):
        current = os.path.basename(self.image_path)
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Image",
            "Enter new filename:",
            text=current
        )
        if not ok or not new_name.strip():
            return

        base, ext = os.path.splitext(current)
        if not new_name.lower().endswith(ext.lower()):
            new_name += ext

        new_path = os.path.join(os.path.dirname(self.image_path), new_name)
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Rename", f"File '{new_name}' already exists.")
            return

        try:
            os.rename(self.image_path, new_path)
            # update in-memory path
            self.image_path = new_path
            self.name_label.setText(new_name)
            self._load_image()
            # schedule metadata update once
            self.rename_debounce_timer.start(500)
        except Exception as e:
            QMessageBox.warning(self, "Rename", f"Could not rename: {e}")

    def _apply_metadata_update(self):
        """Run after debounce to update object_metadata.json and emit signal."""
        old, new = self.original_path, self.image_path
        try:
            data = {}
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            changed = False
            # data is { label: { "images": [...], ... }, ... } or similar
            for entry in data.values():
                images = entry.get("images") or entry.get("image_paths") or []
                for i, p in enumerate(images):
                    if p == old:
                        images[i] = new
                        changed = True
            if changed:
                with open(METADATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            # notify parent
            self.image_renamed.emit(old, new)
            # reset original_path
            self.original_path = new
        except Exception as e:
            QMessageBox.warning(self, "Metadata Update", f"Failed to update metadata: {e}")
