#image_grid.py

from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
import os

class ImageGrid(QWidget):
    """Grid widget to display clickable image thumbnails"""
    image_clicked = pyqtSignal(str)  # Emits the full path of clicked image

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        self.layout.setSpacing(10)
        self.image_labels = []
        self.image_paths = []

    def populate(self, folder, index_data, query=None):
        # Clear existing thumbnails
        for label in self.image_labels:
            label.deleteLater()
        self.image_labels.clear()
        self.image_paths.clear()

        # Filter images based on search query
        filtered = []
        for img_path, data in index_data.items():
            if query:
                objects = data.get("objects", [])
                if any(query in obj.lower() for obj in objects):
                    filtered.append((img_path, data))
            else:
                filtered.append((img_path, data))

        # Populate grid layout
        row, col = 0, 0
        max_cols = 4
        for img_path, data in filtered:
            # Resolve full path
            full_path = os.path.join(folder, img_path) if not os.path.isabs(img_path) else img_path
            if not os.path.exists(full_path):
                continue

            pixmap = QPixmap(full_path)
            if pixmap.isNull():
                continue
            # Scale thumbnail
            pixmap = pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio)

            label = ClickableLabel(self)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedSize(200, 150)
            label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
            label.image_path = full_path
            label.clicked.connect(self.on_image_clicked)

            self.layout.addWidget(label, row, col)
            self.image_labels.append(label)
            self.image_paths.append(full_path)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def on_image_clicked(self, label):
        """Emit the clicked image path"""
        self.image_clicked.emit(label.image_path)


class ClickableLabel(QLabel):
    """Custom QLabel that emits a signal when clicked"""
    clicked = pyqtSignal(object)  # Emits the label instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = None

    def mousePressEvent(self, event):
        # Emit click event withaout calling super to avoid C++ object issues
        self.clicked.emit(self)
