"""
标签页管理模块

该模块实现了多标签页容器，支持标签页的添加、移除、切换和拖拽排序。
"""

import os
from typing import Optional
from PySide6.QtWidgets import QTabWidget, QTabBar
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent

from ui.editor_pane import EditorPane


class TabWidget(QTabWidget):
    """
    标签页容器类
    
    管理多个编辑器窗格的标签页，支持标签页切换、关闭和拖拽排序。
    """
    
    # 信号：标签页关闭请求
    tab_close_requested = Signal(int)
    
    # 信号：当前标签页改变
    current_tab_changed = Signal(int)
    
    # 信号：双击空白区域
    double_click_empty = Signal()
    
    def __init__(self, parent=None):
        """
        初始化标签页容器
        
        Args:
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        # 设置标签页可关闭
        self.setTabsClosable(True)
        
        # 设置标签页可移动（拖拽排序）
        self.setMovable(True)
        
        # 设置文档模式（更好的外观）
        self.setDocumentMode(True)
        
        # 连接信号
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_current_changed)
        
        # 安装事件过滤器到标签栏，处理中键点击和双击
        self.tabBar().installEventFilter(self)
    
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
                        self.tabCloseRequested.emit(index)
                        return True
        
        return super().eventFilter(obj, event)
    
    def add_editor_tab(self, file_path: Optional[str] = None, content: str = "") -> EditorPane:
        """
        添加新的编辑器标签页
        
        Args:
            file_path: 文件路径（可选）
            content: 初始内容
            
        Returns:
            EditorPane: 新创建的编辑器窗格
        """
        # 创建新的编辑器窗格
        editor = EditorPane()
        
        # 设置文件路径
        if file_path:
            editor.set_file_path(file_path)
        
        # 设置内容
        if content:
            editor.setPlainText(content)
            # 重置修改状态
            editor.document().setModified(False)
        
        # 确定标签页标题
        if file_path:
            tab_title = os.path.basename(file_path)
        else:
            # 未命名文件
            tab_title = f"未命名 {self.count() + 1}"
        
        # 添加标签页
        index = self.addTab(editor, tab_title)
        
        # 切换到新标签页
        self.setCurrentIndex(index)
        
        # 连接修改状态信号
        editor.modification_changed.connect(
            lambda modified: self._on_modification_changed(editor, modified)
        )
        
        return editor
    
    def get_current_editor(self) -> Optional[EditorPane]:
        """
        获取当前活动的编辑器窗格
        
        Returns:
            Optional[EditorPane]: 当前编辑器窗格，如果没有则返回 None
        """
        current_widget = self.currentWidget()
        if isinstance(current_widget, EditorPane):
            return current_widget
        return None
    
    def get_editor_at(self, index: int) -> Optional[EditorPane]:
        """
        获取指定索引的编辑器窗格
        
        Args:
            index: 标签页索引
            
        Returns:
            Optional[EditorPane]: 编辑器窗格，如果索引无效则返回 None
        """
        widget = self.widget(index)
        if isinstance(widget, EditorPane):
            return widget
        return None
    
    def close_tab(self, index: int) -> bool:
        """
        关闭指定索引的标签页
        
        Args:
            index: 标签页索引
            
        Returns:
            bool: 如果成功关闭返回 True，否则返回 False
        """
        if index < 0 or index >= self.count():
            return False
        
        # 获取编辑器
        editor = self.get_editor_at(index)
        if not editor:
            return False
        
        # 移除标签页
        self.removeTab(index)
        
        # 删除编辑器窗格
        editor.deleteLater()
        
        return True
    
    def close_current_tab(self) -> bool:
        """
        关闭当前标签页
        
        Returns:
            bool: 如果成功关闭返回 True，否则返回 False
        """
        return self.close_tab(self.currentIndex())
    
    def get_all_editors(self) -> list[EditorPane]:
        """
        获取所有编辑器窗格
        
        Returns:
            list[EditorPane]: 编辑器窗格列表
        """
        editors = []
        for i in range(self.count()):
            editor = self.get_editor_at(i)
            if editor:
                editors.append(editor)
        return editors
    
    def find_tab_by_file_path(self, file_path: str) -> int:
        """
        根据文件路径查找标签页索引
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 标签页索引，如果未找到返回 -1
        """
        for i in range(self.count()):
            editor = self.get_editor_at(i)
            if editor and editor.get_file_path() == file_path:
                return i
        return -1
    
    def _on_tab_close_requested(self, index: int):
        """
        处理标签页关闭请求
        
        Args:
            index: 标签页索引
        """
        # 发射自定义信号
        self.tab_close_requested.emit(index)
    
    def _on_current_changed(self, index: int):
        """
        处理当前标签页改变
        
        Args:
            index: 新的当前标签页索引
        """
        # 发射自定义信号
        self.current_tab_changed.emit(index)
    
    def _on_modification_changed(self, editor: EditorPane, modified: bool):
        """
        处理编辑器修改状态改变
        
        Args:
            editor: 编辑器窗格
            modified: 是否已修改
        """
        # 查找编辑器对应的标签页索引
        for i in range(self.count()):
            if self.widget(i) == editor:
                # 更新标签页标题
                self._update_tab_title(i, editor, modified)
                break
    
    def _update_tab_title(self, index: int, editor: EditorPane, modified: bool):
        """
        更新标签页标题
        
        Args:
            index: 标签页索引
            editor: 编辑器窗格
            modified: 是否已修改
        """
        # 获取基本标题
        file_path = editor.get_file_path()
        if file_path:
            base_title = os.path.basename(file_path)
        else:
            base_title = self.tabText(index).rstrip(" *")
        
        # 添加修改指示器
        if modified:
            title = f"{base_title} *"
        else:
            title = base_title
        
        # 设置标签页标题
        self.setTabText(index, title)
    
    def update_tab_title(self, index: int, title: str):
        """
        更新标签页标题（公共方法）
        
        Args:
            index: 标签页索引
            title: 新标题
        """
        if 0 <= index < self.count():
            editor = self.get_editor_at(index)
            if editor:
                modified = editor.is_modified()
                if modified:
                    title = f"{title} *"
                self.setTabText(index, title)
