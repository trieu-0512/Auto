# Custom UI Widgets for Orbita Multi-Profile Automation

from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt


class StatusBadge(QLabel):
    """Custom status badge widget with color coding."""
    
    STATUS_COLORS = {
        'running': ('#27ae60', '#2ecc71'),
        'active': ('#27ae60', '#2ecc71'),
        'ready': ('#3498db', '#5dade2'),
        'idle': ('#7f8c8d', '#95a5a6'),
        'queued': ('#3498db', '#5dade2'),
        'finished': ('#27ae60', '#2ecc71'),
        'error': ('#c0392b', '#e74c3c'),
        'missing': ('#e67e22', '#f39c12'),
        'inactive': ('#7f8c8d', '#95a5a6'),
        'stopped': ('#f39c12', '#f1c40f'),
    }
    
    def __init__(self, status: str = 'idle', parent=None):
        super().__init__(parent)
        self.setStatus(status)
    
    def setStatus(self, status: str):
        status_lower = status.lower() if status else 'idle'
        colors = self.STATUS_COLORS.get(status_lower, ('#7f8c8d', '#95a5a6'))
        self.setText(status.capitalize() if status else 'Unknown')
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {colors[0]};
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)


class StatsCard(QFrame):
    """Stats card widget for displaying metrics."""
    
    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666666; font-size: 12px; background: transparent;")
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #2196F3; font-size: 28px; font-weight: bold; background: transparent;")
        layout.addWidget(self.value_label)
    
    def setValue(self, value: str):
        self.value_label.setText(value)


class ActionButton(QPushButton):
    """Small action button with icon for table rows."""
    
    BUTTON_STYLES = {
        'browser': {
            'bg': '#2196F3',
            'hover': '#1976D2',
            'text': 'white'
        },
        'folder': {
            'bg': '#FF9800',
            'hover': '#F57C00',
            'text': 'white'
        },
        'run': {
            'bg': '#4CAF50',
            'hover': '#388E3C',
            'text': 'white'
        },
        'default': {
            'bg': '#f5f5f5',
            'hover': '#e0e0e0',
            'text': '#333333'
        }
    }
    
    def __init__(self, icon_text: str, tooltip: str = "", button_type: str = "default", parent=None):
        super().__init__(icon_text, parent)
        self.setToolTip(tooltip)
        self.setFixedSize(36, 28)
        
        style = self.BUTTON_STYLES.get(button_type, self.BUTTON_STYLES['default'])
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {style['bg']};
                border: none;
                border-radius: 4px;
                font-size: 14px;
                color: {style['text']};
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: {style['hover']};
            }}
            QPushButton:pressed {{
                background-color: {style['hover']};
            }}
        """)
