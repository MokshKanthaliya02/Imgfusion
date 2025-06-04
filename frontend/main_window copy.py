# frontend/main_window.py

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QFileDialog, QApplication, QScrollArea, QComboBox, QGridLayout, QToolButton
)
from backend.main_logic import extract_text_tesseract, extract_text_aya_vision
from backend.storage_manager import load_metadata, save_metadata
from frontend.components.image_widget import ImageWidget
from PIL import Image

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
THUMB_DIR = os.path.join(DATA_DIR, 'images')
METADATA_FILE = os.path.join(DATA_DIR, 'metadata.json')

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR Image Search")
        self.resize(1000, 700)

        os.makedirs(THUMB_DIR, exist_ok=True)

        self.metadata = load_metadata(METADATA_FILE)
        self.image_widgets = []

        # --- Top bar: model dropdown + search + clear ---
        self.model_selector = QComboBox()
        self.model_selector.addItems(["Tesseract", "Aya Vision"])

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search text…")
        self.search_bar.returnPressed.connect(self.perform_search)

        self.clear_button = QToolButton()
        self.clear_button.setText("❌")
        self.clear_button.setToolTip("Clear search")
        self.clear_button.clicked.connect(self.clear_search)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.model_selector)
        top_bar.addWidget(self.search_bar)
        top_bar.addWidget(self.clear_button)

        # --- Scrollable image grid ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(15)
        self.scroll_area.setWidget(self.scroll_content)

        # --- Bottom bar: Folder, OCR, Refresh ---
        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.select_folder)

        self.ocr_button = QPushButton("Run OCR")
        self.ocr_button.clicked.connect(self.run_ocr)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_from_metadata)

        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(self.folder_button)
        bottom_bar.addWidget(self.ocr_button)
        bottom_bar.addWidget(self.refresh_button)

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(bottom_bar)
        self.setLayout(main_layout)

        # Load existing data
        self.load_from_metadata()

    def clear_search(self):
        self.search_bar.clear()
        self.perform_search()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder", "")
        if not folder:
            return

        # Clear current UI
        for w in self.image_widgets:
            w.setParent(None)
        self.image_widgets.clear()
        self.metadata.clear()

        # Load all images from folder
        exts = ('.png', '.jpg', '.jpeg')
        row = col = 0
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith(exts):
                full_path = os.path.join(folder, fname)
                widget = ImageWidget(full_path)
                self.grid_layout.addWidget(widget, row, col)
                self.image_widgets.append(widget)

                col += 1
                if col == 4:
                    col = 0
                    row += 1

    def run_ocr(self):
        model = self.model_selector.currentText()
        for widget in self.image_widgets:
            img_path = widget.image_path
            text = (extract_text_tesseract(img_path)
                    if model == "Tesseract"
                    else extract_text_aya_vision(img_path))
            widget.set_text(text)
            self.metadata[img_path] = text

            # Save thumbnail
            thumb_path = os.path.join(THUMB_DIR, os.path.basename(img_path))
            if not os.path.exists(thumb_path):
                img = Image.open(img_path)
                img.thumbnail((220, 160))
                img.save(thumb_path)

        save_metadata(self.metadata, METADATA_FILE)

    def perform_search(self):
        query = self.search_bar.text().lower()
        for widget in self.image_widgets:
            match = query in (widget.ocr_text or "").lower()
            widget.setVisible(match)

    def load_from_metadata(self):
        """Rebuild widgets from metadata and refresh thumbnails."""
        self.image_widgets.clear()
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        row = col = 0
        for img_path, text in self.metadata.items():
            thumb_path = os.path.join(THUMB_DIR, os.path.basename(img_path))
            display_path = thumb_path if os.path.exists(thumb_path) else img_path

            widget = ImageWidget(display_path)
            widget.image_path = img_path
            widget.set_text(text)

            # Force thumbnail refresh
            widget.set_thumbnail(img_path)

            self.grid_layout.addWidget(widget, row, col)
            self.image_widgets.append(widget)

            col += 1
            if col == 4:
                col = 0
                row += 1

    def refresh_from_metadata(self):
        """Reload metadata and refresh the grid and thumbnails."""
        self.metadata = load_metadata(METADATA_FILE)
        self.load_from_metadata()
        self.perform_search()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
