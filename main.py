"""
Publime - SQL编辑器主程序入口
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow


class SingleApplication(QApplication):
    """单实例应用程序类"""
    
    def __init__(self, argv, key):
        super().__init__(argv)
        self._key = key
        self._server = None
        self._is_running = False
        
        # 尝试连接到已存在的实例
        socket = QLocalSocket()
        socket.connectToServer(self._key)
        
        if socket.waitForConnected(500):
            # 已有实例在运行
            self._is_running = True
            # 发送文件路径给已存在的实例
            files_to_open = []
            for arg in argv[1:]:
                if os.path.isfile(arg):
                    files_to_open.append(os.path.abspath(arg))
            
            if files_to_open:
                message = '\n'.join(files_to_open)
                socket.write(message.encode('utf-8'))
                socket.waitForBytesWritten(1000)
            
            socket.disconnectFromServer()
        else:
            # 没有实例在运行，创建服务器
            self._server = QLocalServer()
            # 移除旧的服务器
            QLocalServer.removeServer(self._key)
            self._server.listen(self._key)
            self._server.newConnection.connect(self._handle_new_connection)
    
    def is_running(self):
        """检查是否已有实例在运行"""
        return self._is_running
    
    def _handle_new_connection(self):
        """处理新连接（来自另一个实例）"""
        socket = self._server.nextPendingConnection()
        if socket:
            socket.waitForReadyRead(1000)
            data = socket.readAll().data().decode('utf-8')
            if data:
                # 解析文件路径
                files = data.strip().split('\n')
                # 获取主窗口并打开文件
                for widget in self.topLevelWidgets():
                    if isinstance(widget, MainWindow):
                        for file_path in files:
                            if os.path.isfile(file_path):
                                widget.open_file(file_path)
                        widget.raise_()
                        widget.activateWindow()
                        break
            socket.disconnectFromServer()


def main():
    """主函数"""
    # 创建单实例应用
    app = SingleApplication(sys.argv, "Publime_SingleInstance")
    
    # 如果已有实例在运行，退出
    if app.is_running():
        return 0
    
    app.setApplicationName("Publime")
    app.setOrganizationName("Publime")
    
    # 检查命令行参数中是否有文件路径
    files_to_open = []
    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            files_to_open.append(arg)
    
    # 创建主窗口，传递是否有命令行文件的标志
    window = MainWindow(has_command_line_files=len(files_to_open) > 0)
    
    # 打开命令行指定的文件
    for file_path in files_to_open:
        window.open_file(file_path)
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
