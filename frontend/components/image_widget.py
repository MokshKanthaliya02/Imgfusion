from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect,
    QDialog, QHBoxLayout, QScrollArea, QTextEdit, QPushButton,
    QFileDialog
)
from PyQt6.QtGui import QPixmap, QImage, QColor, QTransform
from PyQt6.QtCore import Qt
import cv2


class ImageWidget(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.ocr_text = ""

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setFixedSize(280, 220)
        self.image_label.setStyleSheet("border: 2px solid #444; border-radius: 8px; background-color: #222;")
        self.layout.addWidget(self.image_label)

        self.set_thumbnail(image_path)
        self.image_label.mousePressEvent = self.open_fullscreen_dialog
        self.shadow_effect = None

    def set_thumbnail(self, path):
        img = cv2.imread(path)
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img.shape
            bytes_per_line = ch * w
            qimg = QImage(img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg).scaled(
                280, 220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)

    def set_text(self, text):
        self.ocr_text = text
        self.image_label.setToolTip(text)

    def enterEvent(self, event):
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(15)
        self.shadow_effect.setOffset(0, 0)
        self.shadow_effect.setColor(QColor(0, 150, 255, 180))
        self.image_label.setGraphicsEffect(self.shadow_effect)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.image_label.setGraphicsEffect(None)
        self.shadow_effect = None
        return super().leaveEvent(event)

    def open_fullscreen_dialog(self, event):
        dialog = QDialog(self)
        dialog.setWindowTitle("Full Image with OCR Text")
        dialog.setMinimumSize(1000, 700)

        layout = QHBoxLayout(dialog)
        image_side_layout = QVBoxLayout()

        # Scrollable image display
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        full_image_label = QLabel()
        full_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_scroll.setWidget(full_image_label)

        # Load original and rotated pixmap
        original_pixmap = QPixmap(self.image_path)
        rotated_pixmap = original_pixmap
        rotation_angle = 0
        full_image_label.setPixmap(rotated_pixmap)

        # Toggle: Fit to window vs actual size
        toggle_button = QPushButton("Fit to Window")
        toggle_button.setCheckable(True)

        def update_pixmap():
            pix = rotated_pixmap
            if toggle_button.isChecked():
                toggle_button.setText("Actual Size")
                pix = pix.scaled(
                    image_scroll.viewport().size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                toggle_button.setText("Fit to Window")
            full_image_label.setPixmap(pix)

        toggle_button.clicked.connect(update_pixmap)

        # Rotate button
        rotate_button = QPushButton("Rotate ⟳")

        def rotate_image():
            nonlocal rotated_pixmap, rotation_angle
            rotation_angle = (rotation_angle + 90) % 360
            transform = QTransform().rotate(90)
            rotated_pixmap = rotated_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            update_pixmap()

        rotate_button.clicked.connect(rotate_image)

        # Save button
        save_button = QPushButton("Save Rotated Image")

        def save_image():
            nonlocal rotated_pixmap
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Save Rotated Image",
                "rotated_image.jpg",
                "JPEG Files (*.jpg);;PNG Files (*.png);;All Files (*)"
            )
            if file_path:
                # Determine extension from selected filter if not provided
                if not (file_path.lower().endswith(".jpg") or file_path.lower().endswith(".png")):
                    if "PNG" in selected_filter:
                        file_path += ".png"
                    else:
                        file_path += ".jpg"
                rotated_pixmap.save(file_path)

        save_button.clicked.connect(save_image)

        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(toggle_button)
        controls_layout.addWidget(rotate_button)
        controls_layout.addWidget(save_button)

        image_side_layout.addWidget(image_scroll)
        image_side_layout.addLayout(controls_layout)


        # OCR text panel
        text_edit = QTextEdit()
        text_edit.setText(self.ocr_text or "[No text extracted yet]")
        text_edit.setReadOnly(True)
        text_edit.setMinimumWidth(400)
        text_edit.setStyleSheet("font-family: Consolas; font-size: 14px;")

        layout.addLayout(image_side_layout, stretch=2)
        layout.addWidget(text_edit, stretch=1)

        dialog.exec()
