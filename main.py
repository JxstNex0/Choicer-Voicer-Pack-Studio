"""
Choicer Voicer Pack Studio - Standalone Desktop Application
Entry Point
"""

import sys
import os

# Ensure local package path is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Choicer Voicer Pack Studio")
    app.setOrganizationName("YeahMaybe")

    # Set App Icon if exists
    icon_path = os.path.join(current_dir, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
