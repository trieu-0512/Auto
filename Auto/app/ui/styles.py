# UI Styles for Orbita Multi-Profile Automation
# Clean white theme

LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #333333;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QFrame {
    background-color: #ffffff;
}

QFrame#header {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    padding: 8px;
}

QLabel#appTitle {
    font-size: 18px;
    font-weight: bold;
    color: #2196F3;
}

QTabWidget::pane {
    border: none;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f5f5f5;
    color: #666666;
    padding: 12px 24px;
    margin-right: 2px;
    border: 1px solid #e0e0e0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #2196F3;
    color: white;
    border-color: #2196F3;
}

QTabBar::tab:hover:!selected {
    background-color: #e3f2fd;
}

QPushButton {
    background-color: #f5f5f5;
    color: #333333;
    border: 1px solid #d0d0d0;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e8e8e8;
    border-color: #2196F3;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton#primaryBtn {
    background-color: #2196F3;
    color: white;
    border: none;
}

QPushButton#primaryBtn:hover {
    background-color: #1976D2;
}

QPushButton#dangerBtn {
    background-color: #f44336;
    color: white;
    border: none;
}

QPushButton#dangerBtn:hover {
    background-color: #d32f2f;
}

QPushButton#successBtn {
    background-color: #4CAF50;
    color: white;
    border: none;
}

QPushButton#successBtn:hover {
    background-color: #388E3C;
}

QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 8px 12px;
    color: #333333;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #2196F3;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    gridline-color: #f0f0f0;
    alternate-background-color: #ffffff;
    selection-background-color: #2196F3;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 10px;
    border-bottom: 1px solid #f0f0f0;
    background-color: #ffffff;
    color: #333333;
}

QTableWidget::item:selected {
    background-color: #2196F3;
    color: #ffffff;
}

QTableWidget::item:hover:!selected {
    background-color: #f5f5f5;
}

QHeaderView::section {
    background-color: #fafafa;
    color: #666666;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #e0e0e0;
    font-weight: bold;
}

QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #d0d0d0;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #2196F3;
}

QScrollBar:horizontal {
    background-color: #f5f5f5;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #d0d0d0;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #2196F3;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: bold;
}

QGroupBox::title {
    color: #2196F3;
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #f0f0f0;
    color: #333333;
    background-color: #ffffff;
}

QListWidget::item:selected {
    background-color: #2196F3;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #f5f5f5;
}

QStatusBar {
    background-color: #ffffff;
    color: #666666;
    border-top: 1px solid #e0e0e0;
}

QToolTip {
    background-color: #333333;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px;
}

QProgressBar {
    background-color: #e0e0e0;
    border: none;
    border-radius: 4px;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #2196F3;
    border-radius: 4px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #d0d0d0;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2196F3;
    border-color: #2196F3;
}

QCheckBox::indicator:hover {
    border-color: #2196F3;
}
"""

# Keep dark style as option
DARK_STYLE = LIGHT_STYLE  # Use light style by default
