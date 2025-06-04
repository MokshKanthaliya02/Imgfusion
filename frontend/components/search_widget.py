from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QToolButton
from PyQt6.QtCore import pyqtSignal, Qt

class SearchWidget(QWidget):
    """Custom search widget with search box and clear button"""
    
    search_changed = pyqtSignal(str)
    search_triggered = pyqtSignal()  # New signal for search actions
    
    def __init__(self, parent=None, placeholder="Search objects..."):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.returnPressed.connect(self.on_search)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input)
        
        # Clear button
        self.clear_button = QToolButton()
        self.clear_button.setText("❌")
        self.clear_button.setToolTip("Clear search")
        self.clear_button.clicked.connect(self.clear_search)
        layout.addWidget(self.clear_button)
        
    def on_search(self):
        """Emit search signal when user presses Enter"""
        self.search_triggered.emit()
    
    def clear_search(self):
        """Clear search input and trigger search update"""
        self.search_input.clear()
        self.search_triggered.emit()
    
    def on_search_changed(self, text):
        """Emit signal when search text changes"""
        self.search_changed.emit(text)
    
    def get_search_text(self):
        """Get current search text"""
        return self.search_input.text()