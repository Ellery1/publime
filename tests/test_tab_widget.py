"""
标签页管理测试模块

测试标签页容器的添加、移除、切换和修改状态指示功能。
"""

import pytest
from PySide6.QtWidgets import QApplication

from ui.tab_widget import TabWidget
from ui.editor_pane import EditorPane


@pytest.fixture
def app(qapp):
    """Qt 应用程序 fixture"""
    return qapp


@pytest.fixture
def tab_widget(app):
    """标签页容器 fixture"""
    widget = TabWidget()
    return widget


def test_tab_widget_creation(tab_widget):
    """测试标签页容器创建"""
    assert tab_widget is not None
    assert isinstance(tab_widget, TabWidget)
    assert tab_widget.count() == 0


def test_add_editor_tab_without_file(tab_widget):
    """测试添加未命名标签页"""
    editor = tab_widget.add_editor_tab()
    
    # 验证标签页已添加
    assert tab_widget.count() == 1
    assert isinstance(editor, EditorPane)
    
    # 验证标签页标题
    assert "未命名" in tab_widget.tabText(0)


def test_add_editor_tab_with_file(tab_widget):
    """测试添加带文件路径的标签页"""
    file_path = "/path/to/test.py"
    editor = tab_widget.add_editor_tab(file_path=file_path)
    
    # 验证标签页已添加
    assert tab_widget.count() == 1
    
    # 验证标签页标题是文件名
    assert tab_widget.tabText(0) == "test.py"
    
    # 验证编辑器文件路径
    assert editor.get_file_path() == file_path


def test_add_editor_tab_with_content(tab_widget):
    """测试添加带初始内容的标签页"""
    content = "Hello, World!"
    editor = tab_widget.add_editor_tab(content=content)
    
    # 验证内容已设置
    assert editor.toPlainText() == content
    
    # 验证未标记为已修改
    assert not editor.is_modified()


def test_add_multiple_tabs(tab_widget):
    """测试添加多个标签页"""
    editor1 = tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    editor2 = tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    editor3 = tab_widget.add_editor_tab(file_path="/path/to/file3.py")
    
    # 验证标签页数量
    assert tab_widget.count() == 3
    
    # 验证标签页标题
    assert tab_widget.tabText(0) == "file1.py"
    assert tab_widget.tabText(1) == "file2.py"
    assert tab_widget.tabText(2) == "file3.py"


def test_get_current_editor(tab_widget):
    """测试获取当前编辑器"""
    editor1 = tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    editor2 = tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    
    # 当前应该是最后添加的标签页
    current = tab_widget.get_current_editor()
    assert current == editor2
    
    # 切换到第一个标签页
    tab_widget.setCurrentIndex(0)
    current = tab_widget.get_current_editor()
    assert current == editor1


def test_get_editor_at(tab_widget):
    """测试获取指定索引的编辑器"""
    editor1 = tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    editor2 = tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    
    # 验证获取正确的编辑器
    assert tab_widget.get_editor_at(0) == editor1
    assert tab_widget.get_editor_at(1) == editor2
    
    # 验证无效索引返回 None
    assert tab_widget.get_editor_at(-1) is None
    assert tab_widget.get_editor_at(2) is None


def test_close_tab(tab_widget):
    """测试关闭标签页"""
    tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    tab_widget.add_editor_tab(file_path="/path/to/file3.py")
    
    # 关闭中间的标签页
    result = tab_widget.close_tab(1)
    
    # 验证关闭成功
    assert result is True
    assert tab_widget.count() == 2
    
    # 验证剩余标签页
    assert tab_widget.tabText(0) == "file1.py"
    assert tab_widget.tabText(1) == "file3.py"


def test_close_current_tab(tab_widget):
    """测试关闭当前标签页"""
    tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    
    # 当前是第二个标签页
    assert tab_widget.currentIndex() == 1
    
    # 关闭当前标签页
    result = tab_widget.close_current_tab()
    
    # 验证关闭成功
    assert result is True
    assert tab_widget.count() == 1
    assert tab_widget.tabText(0) == "file1.py"


def test_close_invalid_tab(tab_widget):
    """测试关闭无效索引的标签页"""
    tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    
    # 尝试关闭无效索引
    result = tab_widget.close_tab(-1)
    assert result is False
    
    result = tab_widget.close_tab(10)
    assert result is False
    
    # 验证标签页未被关闭
    assert tab_widget.count() == 1


def test_get_all_editors(tab_widget):
    """测试获取所有编辑器"""
    editor1 = tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    editor2 = tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    editor3 = tab_widget.add_editor_tab(file_path="/path/to/file3.py")
    
    # 获取所有编辑器
    editors = tab_widget.get_all_editors()
    
    # 验证数量和内容
    assert len(editors) == 3
    assert editor1 in editors
    assert editor2 in editors
    assert editor3 in editors


def test_find_tab_by_file_path(tab_widget):
    """测试根据文件路径查找标签页"""
    tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    tab_widget.add_editor_tab(file_path="/path/to/file3.py")
    
    # 查找存在的文件
    index = tab_widget.find_tab_by_file_path("/path/to/file2.py")
    assert index == 1
    
    # 查找不存在的文件
    index = tab_widget.find_tab_by_file_path("/path/to/nonexistent.py")
    assert index == -1


def test_modification_indicator(tab_widget, qtbot):
    """测试修改状态指示器"""
    editor = tab_widget.add_editor_tab(file_path="/path/to/test.py")
    
    # 初始状态：未修改
    assert tab_widget.tabText(0) == "test.py"
    
    # 修改内容
    editor.setPlainText("modified content")
    
    # 等待信号处理
    qtbot.wait(100)
    
    # 验证标题显示修改指示器
    assert tab_widget.tabText(0) == "test.py *"
    
    # 重置修改状态 - 需要手动触发信号
    editor.document().setModified(False)
    editor.modification_changed.emit(False)
    
    # 等待信号处理
    qtbot.wait(100)
    
    # 验证标题移除修改指示器
    assert tab_widget.tabText(0) == "test.py"


def test_tab_switching(tab_widget):
    """测试标签页切换"""
    editor1 = tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    editor2 = tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    
    # 当前是第二个标签页
    assert tab_widget.currentIndex() == 1
    assert tab_widget.get_current_editor() == editor2
    
    # 切换到第一个标签页
    tab_widget.setCurrentIndex(0)
    assert tab_widget.currentIndex() == 0
    assert tab_widget.get_current_editor() == editor1


def test_empty_tab_widget(tab_widget):
    """测试空标签页容器"""
    # 验证空容器
    assert tab_widget.count() == 0
    assert tab_widget.get_current_editor() is None
    assert tab_widget.get_all_editors() == []


def test_update_tab_title(tab_widget, qtbot):
    """测试更新标签页标题"""
    editor = tab_widget.add_editor_tab(file_path="/path/to/test.py", content="initial")
    
    # 更新标题
    tab_widget.update_tab_title(0, "new_name.py")
    assert tab_widget.tabText(0) == "new_name.py"
    
    # 通过用户输入方式修改内容（这会触发修改状态）
    cursor = editor.textCursor()
    cursor.insertText(" modified")
    
    # 等待信号处理
    qtbot.wait(100)
    
    # 验证编辑器确实被标记为已修改
    assert editor.is_modified() is True
    
    # 更新标题 - 应该保留修改指示器
    tab_widget.update_tab_title(0, "new_name.py")
    assert tab_widget.tabText(0) == "new_name.py *"


def test_tab_close_requested_signal(tab_widget, qtbot):
    """测试标签页关闭请求信号"""
    tab_widget.add_editor_tab(file_path="/path/to/test.py")
    
    # 监听信号
    with qtbot.waitSignal(tab_widget.tab_close_requested, timeout=1000) as blocker:
        # 触发关闭请求
        tab_widget.tabCloseRequested.emit(0)
    
    # 验证信号参数
    assert blocker.args == [0]


def test_current_tab_changed_signal(tab_widget, qtbot):
    """测试当前标签页改变信号"""
    tab_widget.add_editor_tab(file_path="/path/to/file1.py")
    tab_widget.add_editor_tab(file_path="/path/to/file2.py")
    
    # 监听信号
    with qtbot.waitSignal(tab_widget.current_tab_changed, timeout=1000) as blocker:
        # 切换标签页
        tab_widget.setCurrentIndex(0)
    
    # 验证信号参数
    assert blocker.args == [0]
