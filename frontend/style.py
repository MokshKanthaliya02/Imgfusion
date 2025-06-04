"""
Styling constants and utility functions for the application UI
"""

COLORS = {
    "primary": "#3B82F6",       # Blue
    "secondary": "#14B8A6",     # Teal
    "accent": "#F97316",        # Orange
    "success": "#10B981",       # Green
    "warning": "#F59E0B",       # Amber
    "error": "#EF4444",         # Red
    "background": "#F9FAFB",    # Light gray
    "surface": "#FFFFFF",       # White
    "text": {
        "primary": "#1F2937",   # Dark gray
        "secondary": "#4B5563", # Medium gray
        "disabled": "#9CA3AF",  # Light gray
    }
}

STYLE_SHEETS = {
    "main_window": f"""
        QWidget {{
            background-color: {COLORS['background']};
            color: {COLORS['text']['primary']};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
    """,
    
    "title_label": f"""
        QLabel {{
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text']['primary']};
            padding: 10px 0;
        }}
    """,
    
    "subtitle_label": f"""
        QLabel {{
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text']['primary']};
            padding: 5px 0;
        }}
    """,
    
    "search_bar": f"""
        QLineEdit {{
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 8px 12px;
            background-color: white;
            font-size: 14px;
            color: {COLORS['text']['primary']};
        }}
        
        QLineEdit:focus {{
            border: 2px solid {COLORS['primary']};
        }}
    """,
    
    "button": f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background-color: #2563EB;
        }}
        
        QPushButton:pressed {{
            background-color: #1D4ED8;
        }}
        
        QPushButton:disabled {{
            background-color: #9CA3AF;
            color: #F3F4F6;
        }}
    """,
    
    "secondary_button": f"""
        QPushButton {{
            background-color: white;
            color: {COLORS['text']['primary']};
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 14px;
        }}
        
        QPushButton:hover {{
            background-color: #F9FAFB;
            border: 1px solid #9CA3AF;
        }}
        
        QPushButton:pressed {{
            background-color: #F3F4F6;
        }}
    """,
    
    "icon_button": f"""
        QPushButton {{
            background-color: transparent;
            border-radius: 4px;
            padding: 4px;
        }}
        
        QPushButton:hover {{
            background-color: rgba(0, 0, 0, 0.05);
        }}
        
        QPushButton:pressed {{
            background-color: rgba(0, 0, 0, 0.1);
        }}
    """,
    
    "face_label": f"""
        QLabel {{
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text']['primary']};
            padding: 5px 0;
        }}
    """,
    
    "thumbnail": f"""
        QLabel {{
            background-color: white;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 4px;
        }}
        
        QLabel:hover {{
            border: 2px solid {COLORS['primary']};
            padding: 3px;
        }}
    """,
    
    "scroll_area": f"""
        QScrollArea {{
            background-color: {COLORS['background']};
            border: none;
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {COLORS['background']};
            width: 10px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background: #D1D5DB;
            min-height: 30px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: #9CA3AF;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
            background: none;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """,
    
    "status_label": f"""
        QLabel {{
            font-size: 14px;
            color: {COLORS['text']['secondary']};
            padding: 5px;
            border-radius: 4px;
            background-color: rgba(0, 0, 0, 0.03);
        }}
    """
}

def get_style(key):
    """Get a stylesheet by key"""
    return STYLE_SHEETS.get(key, "")