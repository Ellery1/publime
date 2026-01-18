# 中键点击关闭标签功能修复

## 修复日期
2026年1月16日

## 问题描述

**问题**: 用鼠标中键（滚轮）点击标签时，标签没有关闭

**预期行为**: 用鼠标中键点击标签应该立即关闭该标签

**实际行为**: 点击后没有任何反应

## 根本原因

在`ui/tab_widget.py`的`eventFilter`方法中，当检测到中键点击时，代码发射的是自定义信号`tab_close_requested`：

```python
# 错误的代码
self.tab_close_requested.emit(index)
```

但是在`ui/main_window.py`中，连接的是Qt内置的`tabCloseRequested`信号：

```python
self.tab_widget.tabCloseRequested.connect(self.close_tab)
```

**信号名称不匹配**:
- 发射的信号: `tab_close_requested` (自定义信号，下划线命名)
- 连接的信号: `tabCloseRequested` (Qt内置信号，驼峰命名)

由于信号名称不匹配，中键点击事件虽然被捕获了，但发射的信号没有被任何槽函数接收，所以标签不会关闭。

## 修复方案

修改`eventFilter`方法，发射Qt内置的`tabCloseRequested`信号：

```python
def eventFilter(self, obj, event):
    """事件过滤器，处理标签栏的鼠标事件"""
    if obj == self.tabBar():
        if event.type() == event.Type.MouseButtonDblClick:
            # 双击事件
            if event.button() == Qt.MouseButton.LeftButton:
                # 检查是否点击在空白区域
                index = self.tabBar().tabAt(event.pos())
                if index == -1:
                    # 点击在空白区域，发射信号
                    self.double_click_empty.emit()
                    return True
        elif event.type() == event.Type.MouseButtonPress:
            # 鼠标按下事件
            if event.button() == Qt.MouseButton.MiddleButton:
                # 中键点击
                index = self.tabBar().tabAt(event.pos())
                if index >= 0:
                    # 点击在标签上，发射Qt内置的tabCloseRequested信号
                    self.tabCloseRequested.emit(index)  # 修复：使用驼峰命名
                    return True
    
    return super().eventFilter(obj, event)
```

## 修复效果

修复后的行为：
1. 用鼠标中键点击任意标签
2. `tabCloseRequested`信号被发射
3. 主窗口的`close_tab`方法被调用
4. 如果文件有未保存的修改，会弹出保存确认对话框
5. 标签被关闭

## 技术细节

### Qt信号系统

Qt有两种信号：
1. **内置信号**: Qt类自带的信号，如`tabCloseRequested`
2. **自定义信号**: 用户定义的信号，如`tab_close_requested`

在TabWidget类中定义了自定义信号：
```python
class TabWidget(QTabWidget):
    # 自定义信号
    tab_close_requested = Signal(int)
    current_tab_changed = Signal(int)
    double_click_empty = Signal()
```

但Qt的QTabWidget类已经有内置的`tabCloseRequested`信号，当用户点击标签上的关闭按钮时会自动发射。

### 为什么使用内置信号

使用Qt内置的`tabCloseRequested`信号有以下优点：
1. **兼容性**: 主窗口已经连接了这个信号
2. **一致性**: 点击关闭按钮和中键点击使用相同的信号
3. **简单性**: 不需要额外的信号连接

### 事件流程

完整的中键点击事件流程：
1. 用户用鼠标中键点击标签
2. `MouseButtonPress`事件被触发
3. `eventFilter`捕获事件
4. 检查是否是中键（`MiddleButton`）
5. 获取点击位置的标签索引
6. 发射`tabCloseRequested(index)`信号
7. 主窗口的`close_tab(index)`方法被调用
8. 检查文件是否有未保存的修改
9. 关闭标签

## 测试方法

### 手动测试
1. 运行程序: `python main.py`
2. 打开多个文件（或新建多个文件）
3. 用鼠标中键（滚轮）点击任意标签
4. 验证标签被关闭
5. 如果文件有修改，验证弹出保存确认对话框

### 测试场景
- ✓ 中键点击未修改的文件 -> 直接关闭
- ✓ 中键点击已修改的文件 -> 弹出保存确认对话框
- ✓ 中键点击最后一个标签 -> 关闭后自动创建新文件
- ✓ 中键点击空白区域 -> 无反应（正确）

## 相关功能

此修复确保了以下功能正常工作：
- 鼠标中键点击关闭标签
- 点击标签上的X按钮关闭标签（原有功能）
- 双击空白区域新建文件（原有功能）
- 文件修改状态检查和保存确认

## 修改的文件
- `ui/tab_widget.py` - 修改`eventFilter`方法，发射正确的信号

## 总结

通过将自定义信号`tab_close_requested`改为Qt内置信号`tabCloseRequested`，修复了中键点击关闭标签的功能。这是一个简单但重要的修复，提升了用户体验，使编辑器的操作更加符合用户习惯。
