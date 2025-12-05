# Orbita Multi-Profile Automation
# Main entry point

import sys
from PyQt5.QtWidgets import QApplication
from app.ui.styles import DARK_STYLE
from app.ui.main_window import MainWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
