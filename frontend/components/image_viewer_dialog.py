import os
import json
import cv2
import numpy as np
import face_recognition
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QComboBox, QDialogButtonBox, QFrame, QInputDialog
)
from PyQt6.QtGui import QImage, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from backend.main_logic import METADATA_PATH, load_face_metadata

class ImageViewerDialog(QDialog):
    """Dialog for viewing full-size images with face recognition highlighting"""
    
    rename_requested = pyqtSignal(str, str)  # image_path, new_face_id
    
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.is_fit_mode = True
        self.face_locations = []
        self.current_face_id = self.get_current_face_id()
        self.available_face_ids = self.get_available_face_ids()
        
        self.setup_ui()
        self.load_image(highlight_faces=True)
        
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Image Viewer")
        self.resize(900, 700)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Image area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area, 1)  # 1 = stretch factor
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Zoom controls
        zoom_controls = QHBoxLayout()
        zoom_controls.setSpacing(4)
        
        self.fit_button = QPushButton("Fit to Window")
        self.fit_button.setIcon(QIcon("frontend/assets/zoom_out.svg"))
        self.fit_button.clicked.connect(self.toggle_fit)
        zoom_controls.addWidget(self.fit_button)
        
        self.actual_size_button = QPushButton("Actual Size")
        self.actual_size_button.setIcon(QIcon("frontend/assets/zoom_in.svg"))
        self.actual_size_button.clicked.connect(lambda: self.toggle_fit(force_actual=True))
        zoom_controls.addWidget(self.actual_size_button)
        
        # Add rename button with edit icon
        self.rename_button = QPushButton("Rename")
        self.rename_button.setIcon(QIcon("frontend/assets/edit.svg"))
        self.rename_button.clicked.connect(self.rename_image)
        zoom_controls.addWidget(self.rename_button)
        
        controls_layout.addLayout(zoom_controls)
        controls_layout.addStretch()
        
        # Face ID controls
        face_controls = QHBoxLayout()
        face_controls.setSpacing(8)
        
        face_id_label = QLabel("Face ID:")
        face_controls.addWidget(face_id_label)
        
        self.face_id_combo = QComboBox()
        self.face_id_combo.setMinimumWidth(200)
        for face_id in sorted(self.available_face_ids):
            self.face_id_combo.addItem(face_id)
        
        # Set current face ID if available
        if self.current_face_id and self.current_face_id in self.available_face_ids:
            self.face_id_combo.setCurrentText(self.current_face_id)
            
        face_controls.addWidget(self.face_id_combo)
        
        self.move_button = QPushButton("Move to Face Group")
        self.move_button.clicked.connect(self.move_to_face_group)
        face_controls.addWidget(self.move_button)
        
        controls_layout.addLayout(face_controls)
        
        layout.addLayout(controls_layout)
        
        # Filename
        self.filename_label = QLabel(os.path.basename(self.image_path))
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.setStyleSheet("""
            color: #4B5563;
            font-size: 12px;
            padding: 8px;
        """)
        layout.addWidget(self.filename_label)
        
        # Close button
        self.close_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.close_button.rejected.connect(self.accept)
        layout.addWidget(self.close_button)
    
    def get_current_face_id(self):
        """Get the current face ID for this image"""
        try:
            with open(METADATA_PATH, "r") as f:
                metadata = json.load(f)
                
            for face_id, data in metadata.items():
                if self.image_path in data.get("images", []):
                    return face_id
                    
        except Exception:
            pass
            
        return None
        
    def get_available_face_ids(self):
        """Get all available face IDs"""
        face_ids = []
        
        try:
            with open(METADATA_PATH, "r") as f:
                metadata = json.load(f)
                face_ids = list(metadata.keys())
        except Exception:
            pass
            
        return face_ids
    
    def load_image(self, highlight_faces=False):
        """Load and display the image, optionally highlighting faces"""
        if not os.path.exists(self.image_path):
            self.image_label.setText("Image not found.")
            return
            
        image = cv2.imread(self.image_path)
        if image is None:
            self.image_label.setText("Unable to load image.")
            return
            
        # Detect faces if requested
        if highlight_faces:
            try:
                # Load current face data
                with open(METADATA_PATH, "r") as f:
                    metadata = json.load(f)
                    
                current_face_id = self.get_current_face_id()
                if current_face_id and current_face_id in metadata:
                    # Get the encoding for this face ID
                    target_encoding = np.array(metadata[current_face_id]["encoding"])
                    
                    # Convert to RGB for face_recognition
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Detect faces in the image
                    self.face_locations = face_recognition.face_locations(rgb_image)
                    face_encodings = face_recognition.face_encodings(rgb_image, self.face_locations)
                    
                    # Draw rectangles around faces
                    for i, (encoding, location) in enumerate(zip(face_encodings, self.face_locations)):
                        # Compare with target encoding
                        match = face_recognition.compare_faces([target_encoding], encoding, tolerance=0.5)[0]
                        
                        # Draw rectangle with color based on match
                        top, right, bottom, left = location
                        if match:
                            color = (0, 255, 0)  # Green for match
                        else:
                            color = (0, 0, 255)  # Red for non-match
                            
                        cv2.rectangle(image, (left, top), (right, bottom), color, 2)
            except Exception as e:
                print(f"Error highlighting faces: {e}")
                
        # Convert to RGB for Qt
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image_rgb.shape
        bytes_per_line = 3 * width
        
        # Convert to QImage and QPixmap
        q_image = QImage(image_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        self.pixmap = QPixmap.fromImage(q_image)
        
        # Apply fit mode if enabled
        self.apply_fit_mode()
    
    def apply_fit_mode(self):
        """Apply the current fit mode to the image display"""
        if self.is_fit_mode:
            # Fit to window
            self.image_label.setPixmap(self.pixmap.scaled(
                self.scroll_area.viewport().size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            self.fit_button.setText("Fit to Window")
            self.fit_button.setIcon(QIcon("frontend/assets/zoom_out.svg"))
        else:
            # Actual size
            self.image_label.setPixmap(self.pixmap)
            self.fit_button.setText("Fit to Window")
            self.fit_button.setIcon(QIcon("frontend/assets/zoom_in.svg"))
    
    def rename_image(self):
        """Prompt the user to rename the image file"""
        current_name = os.path.basename(self.image_path)
        new_name, ok = QInputDialog.getText(self, "Rename Image", "Enter new filename:", text=current_name)

        if ok and new_name:
            new_name = new_name.strip()
            if not new_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                new_name += os.path.splitext(current_name)[1]  # Keep original extension

            # Path in the face_detected folder
            new_path = os.path.join(os.path.dirname(self.image_path), new_name)

            if os.path.exists(new_path):
                self.image_label.setText("Error: File already exists.")
                return

            try:
                # Find the original source file path from metadata
                original_path = None
                original_new_path = None
                
                with open(METADATA_PATH, "r") as f:
                    metadata = json.load(f)
                    
                    # Find the current face ID and update the path in metadata
                    for face_id, data in metadata.items():
                        if self.image_path in data.get("images", []):
                            # Get the index of the current path
                            idx = data["images"].index(self.image_path)
                            
                            # Try to find the original source file
                            base_name = os.path.basename(self.image_path)
                            for root, _, files in os.walk(self.parent().folder_path):
                                if base_name in files:
                                    original_path = os.path.join(root, base_name)
                                    original_new_path = os.path.join(root, new_name)
                                    break
                            
                            # Update the path in metadata
                            data["images"][idx] = new_path
                            break
                
                # Rename the file in the face_detected folder
                os.rename(self.image_path, new_path)
                self.image_path = new_path
                
                # Rename the original file if found
                if original_path and os.path.exists(original_path):
                    if os.path.exists(original_new_path):
                        print(f"Warning: Original destination file already exists: {original_new_path}")
                    else:
                        os.rename(original_path, original_new_path)
                
                # Save updated metadata
                with open(METADATA_PATH, "w") as f:
                    json.dump(metadata, f, indent=4)
                    
                self.filename_label.setText(new_name)
                self.load_image(highlight_faces=True)
                
            except Exception as e:
                self.image_label.setText(f"Error renaming file: {e}")        
    def toggle_fit(self, force_actual=False):
        """Toggle between fit-to-window and actual size modes"""
        self.is_fit_mode = not self.is_fit_mode if not force_actual else False
        self.apply_fit_mode()
    
    def resizeEvent(self, event):
        """Handle resize events to maintain fit-to-window"""
        if self.is_fit_mode:
            self.apply_fit_mode()
        super().resizeEvent(event)
    
    def move_to_face_group(self):
        """Move this image to a different face group"""
        new_face_id = self.face_id_combo.currentText()
        
        if not new_face_id or new_face_id == self.current_face_id:
            return
            
        self.rename_requested.emit(self.image_path, new_face_id)
        self.current_face_id = new_face_id
        self.accept()  # Close dialog after moving