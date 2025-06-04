import sys
from PyQt6.QtWidgets import QApplication, QTabWidget, QMainWindow
from frontend.main_window import MainWindow as FaceRecognitionWindow
from frontend.object_detection import ObjectSearchApp
from frontend.ocr_window import OCRWindow

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Analysis Suite")
        self.resize(1200, 800)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create instances of all apps
        self.face_recognition = FaceRecognitionWindow()
        self.object_detection = ObjectSearchApp()
        self.ocr_window = OCRWindow()
        
        # Add tabs
        self.tabs.addTab(self.face_recognition, "Face Recognition")
        self.tabs.addTab(self.object_detection, "Object Detection")
        self.tabs.addTab(self.ocr_window, "OCR Search")

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()