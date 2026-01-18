# 单实例应用功能说明

## 功能概述

实现了单实例应用机制，确保同一时间只运行一个 Publime 实例。当用户双击文件打开时，如果 Publime 已经在运行，新文件会在现有窗口中以新标签页的形式打开，而不是创建新的应用窗口。

## 实现原理

### 技术方案
使用 PySide6 的 `QLocalServer` 和 `QLocalSocket` 实现进程间通信（IPC）：

1. **首次启动**：创建一个本地服务器（`QLocalServer`），监听名为 "PublimeTextEditor" 的连接
2. **后续启动**：尝试连接到已存在的服务器
   - 如果连接成功 → 说明已有实例在运行，发送文件路径后退出
   - 如果连接失败 → 说明没有实例在运行，创建新的服务器

### 核心代码

```python
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
            # 已有实例在运行，发送文件路径
            self._is_running = True
            if len(sys.argv) > 1:
                message = '\n'.join(sys.argv[1:])
                socket.write(message.encode('utf-8'))
                socket.flush()
            socket.disconnectFromServer()
        else:
            # 创建新服务器
            self._server = QLocalServer()
            QLocalServer.removeServer(self._server_name)
            if self._server.listen(self._server_name):
                self._server.newConnection.connect(self._handle_new_connection)
```

## 用户体验

### 场景 1：首次打开 Publime
- 用户双击 `Publime.exe`
- 应用正常启动，显示主窗口
- 如果有会话历史，恢复上次打开的文件

### 场景 2：Publime 已运行，双击文件
- 用户双击一个 `.txt` 文件
- 系统尝试启动新的 Publime 实例
- 新实例检测到已有实例在运行
- 新实例将文件路径发送给已运行的实例
- 新实例退出
- 已运行的实例接收到文件路径，在新标签页中打开文件
- 已运行的实例窗口被激活并置于前台

### 场景 3：同时双击多个文件
- 用户选中多个文件，右键 → 打开方式 → Publime
- 如果 Publime 已运行，所有文件都会在现有窗口中以多个标签页打开
- 如果 Publime 未运行，启动新实例并打开所有文件

## 优势

1. **节省系统资源**：避免多个实例同时运行
2. **统一工作空间**：所有文件集中在一个窗口管理
3. **更好的用户体验**：符合现代文本编辑器的标准行为（如 VS Code、Sublime Text）
4. **会话管理**：所有打开的文件都在同一个会话中

## 技术细节

### 进程间通信流程

```
新实例启动
    ↓
尝试连接到 "PublimeTextEditor" 服务器
    ↓
连接成功？
    ├─ 是 → 发送文件路径 → 退出进程
    └─ 否 → 创建服务器 → 启动主窗口

已运行实例
    ↓
监听新连接
    ↓
接收到连接
    ↓
读取文件路径
    ↓
在主线程中打开文件（使用 QTimer.singleShot）
    ↓
激活窗口（show, raise, activateWindow）
```

### 线程安全

使用 `QTimer.singleShot(0, lambda: ...)` 确保文件打开操作在主线程中执行，避免跨线程 UI 操作导致的问题。

### 服务器清理

在创建新服务器前调用 `QLocalServer.removeServer()` 清理可能存在的旧服务器实例（如应用崩溃后遗留的）。

## 测试建议

1. **基本功能测试**：
   - 启动 Publime
   - 双击一个文本文件
   - 验证文件在现有窗口中打开

2. **多文件测试**：
   - 启动 Publime
   - 选中多个文件，右键打开
   - 验证所有文件都在现有窗口中打开

3. **窗口激活测试**：
   - 启动 Publime 并最小化
   - 双击一个文件
   - 验证窗口被激活并置于前台

4. **崩溃恢复测试**：
   - 强制结束 Publime 进程
   - 重新启动 Publime
   - 验证可以正常启动（旧服务器已清理）

## 修改的文件

- `main.py` - 实现 `SingleApplication` 类和单实例逻辑

## Git 提交记录

```
df8e2b2 - feat: Implement single instance application with inter-process communication
496815b - docs: Update documentation for single instance feature
```

## 打包结果

- 新的 `dist/Publime.exe` 已生成（44,034,703 字节）
- 包含 `PySide6.QtNetwork` 模块用于网络通信
