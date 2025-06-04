import os
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from frontend.style import get_style

class ThumbnailWidget(QWidget):
    """Widget for displaying a thumbnail image with hover effects"""
    
    thumbnail_clicked = pyqtSignal(str)  # Signal emitting the image path
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        
        # Thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setStyleSheet(get_style("thumbnail"))
        self.thumbnail.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Load image
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                160, 160, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumbnail.setPixmap(pixmap)
            
        self.thumbnail.setFixedSize(170, 170)
        self.thumbnail.setToolTip(os.path.basename(self.image_path))
        
        # File name label (truncated)
        filename = os.path.basename(self.image_path)
        if len(filename) > 20:
            filename = filename[:18] + "..."
            
        self.filename_label = QLabel(filename)
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.setToolTip(os.path.basename(self.image_path))
        self.filename_label.setStyleSheet("""
            color: #4B5563;
            font-size: 12px;
        """)
        
        # Add to layout
        self.layout.addWidget(self.thumbnail, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.filename_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.thumbnail_clicked.emit(self.image_path)
        super().mousePressEvent(event)