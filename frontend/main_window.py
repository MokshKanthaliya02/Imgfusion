import os
import csv
import datetime
import shutil
import json
from PyQt6.QtGui import QImage, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog,
    QPushButton, QGridLayout, QScrollArea, QInputDialog, QDialog,
    QDialogButtonBox, QLineEdit, QSpacerItem, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve
from backend.main_logic import (
    detect_and_cluster_faces,
    rename_face_id,
    load_face_metadata,
    get_images_missing_from_metadata,
    METADATA_PATH
)
from frontend.style import get_style, COLORS
from frontend.components.thumbnail_widget import ThumbnailWidget
from frontend.components.image_viewer_dialog import ImageViewerDialog
from frontend.components.search_widget import SearchWidget

CSV_METADATA_FILE = "face_metadata.csv"

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Face Recognition & Clustering")
        self.resize(1200, 800)
        self.setAcceptDrops(True)
        self.setStyleSheet(get_style("main_window"))
        
        self.folder_path = ""
        self.thumbnail_paths = {}
        self.setup_ui()
        
        # Fade in animation on startup
        self.setWindowOpacity(0)
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(100, self.animation.start)

    def setup_ui(self):
        """Set up the main user interface"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(16)
        
        # Header section
        self.setup_header()
        
        # Search and control section
        self.setup_search_controls()
        
        # Main content area
        self.setup_content_area()
        
        # Footer with action buttons
        self.setup_footer()
        
    def setup_header(self):
        """Set up the header section with title and status"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # App title
        title_label = QLabel("Face Recognition & Clustering")
        title_label.setStyleSheet(get_style("title_label"))
        header_layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Select a folder to begin.")
        self.status_label.setStyleSheet(get_style("status_label"))
        header_layout.addWidget(self.status_label)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"background-color: #E5E7EB;")
        header_layout.addWidget(separator)
        
        self.layout.addLayout(header_layout)
        
    def setup_search_controls(self):
        """Set up the search bar and control buttons"""
        # Search and refresh
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        # Search widget with icon
        self.search_widget = SearchWidget(self, placeholder="Search faces...")
        self.search_widget.search_triggered.connect(lambda text: self.search_faces(text))
        self.search_widget.search_changed.connect(lambda text: self.search_faces(text))
        search_layout.addWidget(self.search_widget)
        
        # Refresh button
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(QIcon("frontend/assets/refresh.svg"))
        self.refresh_button.setIconSize(QSize(20, 20))
        self.refresh_button.setFixedSize(36, 36)
        self.refresh_button.setToolTip("Refresh")
        self.refresh_button.setStyleSheet(get_style("icon_button"))
        self.refresh_button.clicked.connect(self.refresh_metadata)
        search_layout.addWidget(self.refresh_button)
        
        self.layout.addLayout(search_layout)
        
    def setup_content_area(self):
        """Set up the main content area with scroll area and grid layout"""
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(get_style("scroll_area"))
        
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet(f"background-color: {COLORS['background']};")
        
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setVerticalSpacing(16)
        self.grid_layout.setHorizontalSpacing(16)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        
        self.scroll.setWidget(self.grid_widget)
        self.layout.addWidget(self.scroll)
        
    def setup_footer(self):
        """Set up the footer with action buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Create buttons
        self.select_button = QPushButton("Select Folder")
        self.select_button.setStyleSheet(get_style("button"))
        self.select_button.clicked.connect(self.select_folder)
        
        self.detect_button = QPushButton("Detect and Sort Faces")
        self.detect_button.setStyleSheet(get_style("button"))
        self.detect_button.clicked.connect(self.detect_and_show)
        
        # Add buttons to layout
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.detect_button)
        
        self.layout.addLayout(button_layout)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.folder_path = path
                self.status_label.setText(f"Folder: {os.path.basename(path)}")
                self.detect_and_show()
            elif os.path.isfile(path) and path.lower().endswith(('.jpg', '.jpeg', '.png')):
                self.folder_path = os.path.dirname(path)
                self.status_label.setText(f"Processing file from: {os.path.basename(self.folder_path)}")
                self.detect_and_show()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.folder_path = folder
        self.status_label.setText(f"Selected folder: {os.path.basename(folder)}")

        # Add new images to metadata CSV
        self.update_csv_metadata(folder)
        
        # Load preview if metadata exists
        if os.path.exists(METADATA_PATH):
            self.thumbnail_paths, msg = load_face_metadata()
            self.clear_grid()
            self.populate_grid(self.thumbnail_paths)
            self.status_label.setText(msg)
        else:
            self.status_label.setText("No face metadata found. Click 'Detect and Sort Faces' to begin.")
    
    def update_csv_metadata(self, folder):
        """Update CSV metadata with new images and return number of new entries"""
        image_files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]

        # Load existing paths from CSV
        existing_paths = set()
        if os.path.exists(CSV_METADATA_FILE):
            with open(CSV_METADATA_FILE, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_paths.add(os.path.normpath(row['image_path']))

        # Append only new paths to CSV
        new_entries = []
        now = datetime.datetime.now()

        for path in image_files:
            norm_path = os.path.normpath(path)
            if norm_path not in existing_paths:
                new_entries.append({
                    'image_path': norm_path,
                    'date': now.strftime("%Y-%m-%d"),
                    'time': now.strftime("%H:%M:%S")
                })
                existing_paths.add(norm_path)

        if new_entries:
            with open(CSV_METADATA_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['image_path', 'date', 'time'])
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerows(new_entries)
            
            self.status_label.setText(f"Added {len(new_entries)} new images to metadata.")
        else:
            self.status_label.setText("No new images found.")
        
        return len(new_entries)
    
    def detect_and_show(self):
        """Process images and display face clusters"""
        if not self.folder_path:
            self.status_label.setText("No folder selected.")
            return

        self.status_label.setText("Processing images... This may take a moment.")
        self.repaint()  # Force UI update
        
        missing_images = get_images_missing_from_metadata(self.folder_path)

        if missing_images:
            self.thumbnail_paths, msg = detect_and_cluster_faces(
                self.folder_path,
                only_process=missing_images
            )
            self.status_label.setText(f"Processed {len(missing_images)} new image(s). Face groups updated.")
        else:
            self.thumbnail_paths, msg = load_face_metadata()
            self.status_label.setText("All images already processed. Showing current face groups.")

        self.clear_grid()
        self.populate_grid(self.thumbnail_paths)

    def refresh_metadata(self):
        """Fully reload UI based on file system changes"""
        if not self.folder_path:
            self.status_label.setText("No folder selected.")
            return

        self.status_label.setText("Refreshing data from disk...")
        self.repaint()  # Force UI update
        
        changes_detected = False
        
        # 1. Re-read image_metadata.csv
        try:
            # Check if CSV file exists and update with any new images
            if os.path.exists(self.folder_path):
                new_entries = self.update_csv_metadata(self.folder_path)
                if new_entries > 0:
                    changes_detected = True
        except Exception as e:
            self.status_label.setText(f"Error refreshing CSV metadata: {str(e)}")
            return
        
        # 2. Check for new images that need processing
        missing_images = get_images_missing_from_metadata(self.folder_path)
        
        # 3. Process new images if any
        if missing_images:
            self.thumbnail_paths, msg = detect_and_cluster_faces(
                self.folder_path,
                only_process=missing_images
            )
            changes_detected = True
            self.status_label.setText(f"Processed {len(missing_images)} new image(s). Face groups updated.")
        else:
            # 4. Re-read face_metadata.json even if no new images
            try:
                # Check if metadata file exists before loading
                if os.path.exists(METADATA_PATH):
                    old_metadata = self.thumbnail_paths.copy() if hasattr(self, 'thumbnail_paths') else {}
                    self.thumbnail_paths, _ = load_face_metadata()
                    
                    # Check if metadata has changed
                    if old_metadata != self.thumbnail_paths:
                        changes_detected = True
                else:
                    self.thumbnail_paths = {}
                    changes_detected = True
            except Exception as e:
                self.status_label.setText(f"Error loading face metadata: {str(e)}")
                return
        
        # 5. Check face_detected directory structure for changes
        try:
            face_dir = "face_detected"
            if os.path.exists(face_dir):
                # Verify all face directories in metadata actually exist
                for face_id in list(self.thumbnail_paths.keys()):
                    face_path = os.path.join(face_dir, face_id)
                    if not os.path.exists(face_path):
                        # Face directory was deleted, remove from metadata
                        self.thumbnail_paths.pop(face_id, None)
                        changes_detected = True
                
                # Check for new face directories not in metadata
                for item in os.listdir(face_dir):
                    item_path = os.path.join(face_dir, item)
                    if os.path.isdir(item_path) and item not in self.thumbnail_paths:
                        # Found a new face directory, add its images to metadata
                        image_paths = []
                        for img in os.listdir(item_path):
                            if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                                image_paths.append(os.path.join(item_path, img))
                        
                        if image_paths:
                            self.thumbnail_paths[item] = image_paths
                            changes_detected = True
                
                # Verify all images in metadata actually exist
                for face_id, paths in list(self.thumbnail_paths.items()):
                    valid_paths = [p for p in paths if os.path.exists(p)]
                    if len(valid_paths) != len(paths):
                        self.thumbnail_paths[face_id] = valid_paths
                        changes_detected = True
                        
                        # Remove face if no images left
                        if not valid_paths:
                            self.thumbnail_paths.pop(face_id, None)
        except Exception as e:
            self.status_label.setText(f"Error checking face directories: {str(e)}")
            return
        
        # 6. Rebuild UI
        self.clear_grid()
        self.populate_grid(self.thumbnail_paths)
        
        # 7. Update status message
        if changes_detected:
            self.status_label.setText("UI refreshed with changes detected.")
        else:
            self.status_label.setText("UI refreshed. No changes detected.")

    def populate_grid(self, data):
        """Populate the grid layout with face clusters"""
        row = 0
        
        if not data:
            empty_label = QLabel("No faces found. Select a folder with images and click 'Detect and Sort Faces'.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                font-size: 16px;
                color: {COLORS['text']['secondary']};
                padding: 40px;
            """)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 5)
            return
            
        for face_id, paths in data.items():
            # Create face group header
            face_header = QWidget()
            header_layout = QHBoxLayout(face_header)
            header_layout.setContentsMargins(0, 16, 0, 8)
            
            face_label = QLabel(f"{face_id} ({len(paths)} images)")
            face_label.setStyleSheet(get_style("face_label"))
            header_layout.addWidget(face_label)
            
            # Rename button
            rename_button = QPushButton()
            rename_button.setIcon(QIcon("frontend/assets/edit.svg"))
            rename_button.setIconSize(QSize(18, 18))
            rename_button.setFixedSize(32, 32)
            rename_button.setToolTip("Rename Face Group")
            rename_button.setStyleSheet(get_style("icon_button"))
            rename_button.clicked.connect(lambda _, fid=face_id: self.rename_face_dialog(fid))
            header_layout.addWidget(rename_button)
            
            header_layout.addStretch(1)
            
            self.grid_layout.addWidget(face_header, row, 0, 1, 5)
            row += 1
            
            # Add horizontal separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            separator.setStyleSheet("background-color: #E5E7EB; margin: 0 8px;")
            self.grid_layout.addWidget(separator, row, 0, 1, 5)
            row += 1

            # Add thumbnails
            col = 0
            for path in paths:
                if not os.path.exists(path):
                    continue
                    
                thumb_widget = ThumbnailWidget(path)
                thumb_widget.thumbnail_clicked.connect(self.show_full_size_image)
                
                self.grid_layout.addWidget(thumb_widget, row, col)
                
                col += 1
                if col >= 5:
                    col = 0
                    row += 1
            
            if col > 0:
                row += 1
                
        # Add final stretch to push content to the top
        self.grid_layout.setRowStretch(row, 1)

    def rename_face_dialog(self, old_face_id):
        """Show dialog to rename a face group"""
        new_face_name, ok = QInputDialog.getText(
            self, 
            "Rename Face Group", 
            f"Rename '{old_face_id}' to:",
            QLineEdit.EchoMode.Normal
        )
        
        if not ok or not new_face_name or new_face_name == old_face_id:
            return

        # Check for duplication before renaming
        if new_face_name in self.thumbnail_paths:
            dialog = QDialog(self)
            dialog.setWindowTitle("Duplicate Name")
            dialog.setFixedWidth(400)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(16)
            
            warning_label = QLabel(f"'{new_face_name}' already exists. Images will be merged.")
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)
            
            confirm_label = QLabel("Type 'merge' to confirm:")
            layout.addWidget(confirm_label)
            
            confirm_input = QLineEdit()
            layout.addWidget(confirm_input)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | 
                QDialogButtonBox.StandardButton.Cancel
            )
            layout.addWidget(buttons)
            
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            
            if dialog.exec() != QDialog.DialogCode.Accepted or confirm_input.text().lower() != "merge":
                self.status_label.setText("Merge canceled.")
                return

        # Perform the rename operation
        self.status_label.setText(f"Renaming '{old_face_id}' to '{new_face_name}'...")
        self.repaint()  # Force UI update
        
        if rename_face_id("face_detected", old_face_id, new_face_name):
            self.thumbnail_paths, _ = load_face_metadata()
            self.clear_grid()
            self.populate_grid(self.thumbnail_paths)
            self.status_label.setText(f"Successfully renamed '{old_face_id}' to '{new_face_name}'.")
        else:
            self.status_label.setText(f"Failed to rename '{old_face_id}'.")

    def clear_grid(self):
        """Clear all widgets from the grid layout"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_full_size_image(self, path):
        """Show full size image in a dialog"""
        if not os.path.exists(path):
            self.status_label.setText("Image not found.")
            return
            
        dialog = ImageViewerDialog(path, self)
        dialog.rename_requested.connect(self.rename_single_image)
        dialog.exec()

    def rename_single_image(self, image_path, target_face_id):
        """Move a single image to a different face group"""
        if not os.path.exists(image_path):
            self.status_label.setText(f"Image not found: {image_path}")
            return False
            
        try:
            # Load metadata
            with open(METADATA_PATH, "r") as f:
                metadata = json.load(f)
                
            # Find current face ID for the image
            current_face_id = None
            for face_id, data in metadata.items():
                if image_path in data.get("images", []):
                    current_face_id = face_id
                    break
                    
            if not current_face_id:
                self.status_label.setText("Image not found in metadata.")
                return False
                
            if current_face_id == target_face_id:
                self.status_label.setText("Image is already in that face group.")
                return False
                
            # Create target directory if needed
            target_dir = os.path.join("face_detected", target_face_id)
            os.makedirs(target_dir, exist_ok=True)
            
            # Move the file to the new location
            filename = os.path.basename(image_path)
            new_path = os.path.join(target_dir, filename)
            
            # Handle filename conflicts
            if os.path.exists(new_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1
                    
            # Move file and update metadata
            shutil.move(image_path, new_path)
            
            # Update metadata
            metadata[current_face_id]["images"].remove(image_path)
            
            # If target face ID already exists, add to it
            if target_face_id in metadata:
                metadata[target_face_id]["images"].append(new_path)
            else:
                # Create new face ID entry with current encoding
                metadata[target_face_id] = {
                    "images": [new_path],
                    "encoding": metadata[current_face_id].get("encoding")
                }
                
            # Remove empty face groups
            if not metadata[current_face_id]["images"]:
                metadata.pop(current_face_id)
                
            # Save metadata
            with open(METADATA_PATH, "w") as f:
                json.dump(metadata, f, indent=4)
                
            # Refresh UI
            self.thumbnail_paths, _ = load_face_metadata()
            self.clear_grid()
            self.populate_grid(self.thumbnail_paths)
            
            self.status_label.setText(f"Image moved to '{target_face_id}'.")
            return True
            
        except Exception as e:
            self.status_label.setText(f"Error moving image: {str(e)}")
            return False

    def search_faces(self, text=""):
        """Filter face clusters by search text"""
        if not self.thumbnail_paths:
            return
            
        filtered = {}
        text = text.strip().lower() if text else ""
        
        if not text:  # Show all if search is empty
            self.clear_grid()
            self.populate_grid(self.thumbnail_paths)
            return
            
        for face_id, paths in self.thumbnail_paths.items():
            if text in face_id.lower():
                filtered[face_id] = paths
            else:
                # Check image filenames
                matched = [p for p in paths if text in os.path.basename(p).lower()]
                if matched:
                    filtered[face_id] = matched
                    
        self.clear_grid()
        self.populate_grid(filtered)
        
        if not filtered:
            self.status_label.setText("No matches found.")
