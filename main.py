"""
Pocket AI - Main Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QColor
from gui.app import MainWindow
from qfluentwidgets import qconfig, Theme

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configure Aura Theme
    qconfig.theme = Theme.DARK
    # qconfig.themeColor = QColor(51, 181, 229) # Cyan #33b5e5
    
    # Set default font
    app.setFont(QFont("Segoe UI", 10))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
