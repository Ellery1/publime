"""
Text Editor - A Sublime Text alternative built with Python and PySide6.

This is the main entry point for the text editor application.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """
    Main entry point for the text editor application.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Publime")
    app.setOrganizationName("Publime")
    
    # Initialize and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
