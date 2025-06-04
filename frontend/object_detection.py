# object_detection.py

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QFileDialog, QScrollArea
)
from PyQt6.QtCore import QTimer
from frontend.components.image_grid import ImageGrid
from frontend.components.object_viewer_dialog import ObjectViewerDialog
from backend.detection_thread import ObjectDetectionThread
from backend.index_manager import load_index, save_index

class ObjectSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Object Detection App")
        self.resize(900, 700)

        self.image_folder = "images"
        self.index_data = load_index()
        self.auto_scan_active = False
        self.auto_scan_timer = QTimer(self)
        self.auto_scan_timer.timeout.connect(self.auto_scan)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Search bar and refresh
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for an object…")
        self.search_bar.textChanged.connect(self.search_images)

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedSize(30, 30)
        self.refresh_btn.clicked.connect(self.search_images)

        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.refresh_btn)
        layout.addLayout(search_layout)

        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        # Scroll area for image grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_grid = ImageGrid()
        self.image_grid.image_clicked.connect(self._open_object_viewer)
        self.scroll_area.setWidget(self.image_grid)
        layout.addWidget(self.scroll_area)

        # Buttons
        self.load_button = QPushButton("Load Images and Detect Objects")
        self.load_button.clicked.connect(self.load_and_detect)
        layout.addWidget(self.load_button)

        self.auto_button = QPushButton("Auto Scan (Off)")
        self.auto_button.clicked.connect(self.toggle_auto_scan)
        layout.addWidget(self.auto_button)

        self.setLayout(layout)

        # Initial population
        self.search_images()

    def load_and_detect(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return

        self.image_folder = folder
        self.thread = ObjectDetectionThread(self.image_folder, self.index_data)
        self.thread.progress_update.connect(self.update_status)
        self.thread.detection_complete.connect(self.on_detection_complete)
        self.thread.start()

    def update_status(self, processed, total):
        self.status_label.setText(f"Processing: {processed}/{total} images…")

    def on_detection_complete(self, updated_index):
        self.index_data = updated_index
        save_index(self.index_data)
        self.search_images()
        self.status_label.setText("Detection complete.")

    def search_images(self):
        query = self.search_bar.text().lower().strip()
        filtered_index = {}
        
        if not query:
            # Show all images if no search query
            filtered_index = self.index_data
        else:
            # Filter images based on detected objects
            for img_path, objects in self.index_data.items():
                # Check if any detected object matches the search query
                if any(query in obj.lower() for obj in objects.keys()):
                    filtered_index[img_path] = objects
        
        if not filtered_index and query:
            self.status_label.setText(f"No objects found matching '{query}'")
        else:
            self.status_label.setText("")
            
        self.image_grid.populate(self.image_folder, filtered_index)

    def toggle_auto_scan(self):
        if self.auto_scan_active:
            self.auto_scan_timer.stop()
            self.auto_button.setText("Auto Scan (Off)")
        else:
            self.auto_scan_timer.start(5000)
            self.auto_button.setText("Auto Scan (On)")
        self.auto_scan_active = not self.auto_scan_active

    def auto_scan(self):
        if not os.path.exists(self.image_folder):
            return

        current_images = {
            f for f in os.listdir(self.image_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        }
        indexed = set(self.index_data.keys())
        new_images = current_images - indexed
        if new_images:
            self.thread = ObjectDetectionThread(self.image_folder, self.index_data)
            self.thread.progress_update.connect(self.update_status)
            self.thread.detection_complete.connect(self.on_detection_complete)
            self.thread.start()
        else:
            self.status_label.setText("No new images found for auto-scan.")

    def _open_object_viewer(self, image_path):
        from frontend.components.object_viewer_dialog import ObjectViewerDialog

        dlg = ObjectViewerDialog(image_path, parent=self)
        dlg.image_renamed.connect(self._handle_image_renamed)
        dlg.exec()

    def _handle_image_renamed(self, old_path, new_path):
        # Update index_data keys
        if old_path in self.index_data:
            self.index_data[new_path] = self.index_data.pop(old_path)
        else:
            # Update nested image lists
            for entry in self.index_data.values():
                images = entry.get("images") or entry.get("image_paths") or []
                for i, p in enumerate(images):
                    if p == old_path:
                        images[i] = new_path

        # Persist changes and refresh UI
        save_index(self.index_data)
        self.search_images()
        self.status_label.setText(f"Renamed image: {os.path.basename(old_path)} → {os.path.basename(new_path)}")