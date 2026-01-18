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
    
    # 处理命令行参数（从文件关联打开）
    if len(sys.argv) > 1:
        # 打开命令行指定的文件
        for file_path in sys.argv[1:]:
            if file_path and not file_path.startswith('-'):
                window.open_file(file_path)
    
    window.show()
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
