"""
Text Editor - A Sublime Text alternative built with Python and PySide6.

This is the main entry point for the text editor application.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow


class SingleApplication(QApplication):
    """单实例应用类"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self._server_name = "PublimeTextEditor"
        self._server = None
        self._is_running = False
        self.main_window = None
        
        # 尝试连接到已存在的实例
        socket = QLocalSocket()
        socket.connectToServer(self._server_name)
        
        if socket.waitForConnected(500):
            # 已有实例在运行
            self._is_running = True
            
            # 发送命令行参数到已存在的实例
            if len(sys.argv) > 1:
                message = '\n'.join(sys.argv[1:])
                socket.write(message.encode('utf-8'))
                socket.flush()
                socket.waitForBytesWritten(1000)
            
            socket.disconnectFromServer()
        else:
            # 没有实例在运行，创建服务器
            self._server = QLocalServer()
            # 移除可能存在的旧服务器
            QLocalServer.removeServer(self._server_name)
            
            if self._server.listen(self._server_name):
                self._server.newConnection.connect(self._handle_new_connection)
    
    def is_running(self):
        """检查是否已有实例在运行"""
        return self._is_running
    
    def _handle_new_connection(self):
        """处理新的连接（来自其他实例的消息）"""
        socket = self._server.nextPendingConnection()
        if socket:
            socket.waitForReadyRead(1000)
            data = socket.readAll().data().decode('utf-8')
            
            if data and self.main_window:
                # 解析文件路径并打开
                file_paths = data.strip().split('\n')
                for file_path in file_paths:
                    if file_path and not file_path.startswith('-'):
                        # 使用 QTimer 延迟执行，确保在主线程中打开文件
                        QTimer.singleShot(0, lambda fp=file_path: self.main_window.open_file(fp))
                
                # 激活主窗口
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()
            
            socket.disconnectFromServer()


def main():
    """
    Main entry point for the text editor application.
    """
    app = SingleApplication(sys.argv)
    
    # 如果已有实例在运行，退出当前进程
    if app.is_running():
        return 0
    
    app.setApplicationName("Publime")
    app.setOrganizationName("Publime")
    
    # 检查是否有命令行参数（从文件关联打开）
    has_command_line_files = len(sys.argv) > 1
    
    # Initialize and show main window
    window = MainWindow(has_command_line_files=has_command_line_files)
    app.main_window = window
    
    # 处理命令行参数（从文件关联打开）
    if has_command_line_files:
        # 打开命令行指定的文件
        for file_path in sys.argv[1:]:
            if file_path and not file_path.startswith('-'):
                window.open_file(file_path)
    
    window.show()
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
