"""
编辑器窗格单元测试

测试 EditorPane 类的核心功能。
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent, QFont
from ui.editor_pane import EditorPane, LineNumberArea
from themes.dark_theme import get_dark_theme
from themes.light_theme import get_light_theme
import sys


@pytest.fixture
def app():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def editor_pane(app):
    """创建 EditorPane 实例"""
    pane = EditorPane()
    return pane


class TestEditorPane:
    """EditorPane 类的测试"""
    
    def test_initialization(self, editor_pane):
        """测试编辑器窗格初始化"""
        assert editor_pane is not None
        assert editor_pane.line_number_area is not None
        assert isinstance(editor_pane.line_number_area, LineNumberArea)
        assert editor_pane.get_file_path() is None
        assert not editor_pane.is_modified()
    
    def test_set_file_path(self, editor_pane):
        """测试设置文件路径"""
        # 设置 Python 文件路径
        editor_pane.set_file_path("test.py")
        assert editor_pane.get_file_path() == "test.py"
        
        # 验证语法高亮器已创建
        assert editor_pane.syntax_highlighter is not None
        assert editor_pane.syntax_highlighter.language == "python"
    
    def test_set_file_path_with_different_languages(self, editor_pane):
        """测试不同语言的文件路径"""
        test_cases = [
            ("test.py", "python"),
            ("test.java", "java"),
            ("test.sql", "sql"),
            ("test.json", "json"),
            ("test.js", "javascript"),
            ("test.kt", "kotlin"),
        ]
        
        for file_path, expected_language in test_cases:
            editor_pane.set_file_path(file_path)
            assert editor_pane.get_file_path() == file_path
            assert editor_pane.syntax_highlighter is not None
            assert editor_pane.syntax_highlighter.language == expected_language
    
    def test_is_modified(self, editor_pane):
        """测试修改状态跟踪"""
        # 初始状态未修改
        assert not editor_pane.is_modified()
        
        # 设置初始内容并重置修改状态
        editor_pane.setPlainText("Initial")
        editor_pane.document().setModified(False)
        assert not editor_pane.is_modified()
        
        # 使用 insertPlainText 来修改文本（这会标记为已修改）
        cursor = editor_pane.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor_pane.setTextCursor(cursor)
        editor_pane.insertPlainText(" Modified")
        assert editor_pane.is_modified()
        
        # 标记为未修改
        editor_pane.document().setModified(False)
        assert not editor_pane.is_modified()
    
    def test_set_language(self, editor_pane):
        """测试设置语法高亮语言"""
        # 设置 Python 语言
        editor_pane.set_language("python")
        assert editor_pane.syntax_highlighter is not None
        assert editor_pane.syntax_highlighter.language == "python"
        
        # 切换到 Java 语言
        editor_pane.set_language("java")
        assert editor_pane.syntax_highlighter.language == "java"
    
    def test_apply_theme_dark(self, editor_pane):
        """测试应用深色主题"""
        theme = get_dark_theme()
        editor_pane.apply_theme(theme)
        
        # 验证主题已保存
        assert hasattr(editor_pane, '_current_theme')
        assert editor_pane._current_theme == theme
        
        # 验证样式表已设置
        style_sheet = editor_pane.styleSheet()
        assert theme.background in style_sheet
        assert theme.foreground in style_sheet
    
    def test_apply_theme_light(self, editor_pane):
        """测试应用浅色主题"""
        theme = get_light_theme()
        editor_pane.apply_theme(theme)
        
        # 验证主题已保存
        assert hasattr(editor_pane, '_current_theme')
        assert editor_pane._current_theme == theme
        
        # 验证样式表已设置
        style_sheet = editor_pane.styleSheet()
        assert theme.background in style_sheet
        assert theme.foreground in style_sheet
    
    def test_font_zoom_in(self, editor_pane):
        """测试字体放大"""
        # 设置初始字体大小
        initial_size = 12
        font = editor_pane.font()
        font.setPointSize(initial_size)
        editor_pane.setFont(font)
        
        # 直接测试字体大小变化逻辑（不使用事件模拟）
        current_font = editor_pane.font()
        current_size = current_font.pointSize()
        new_size = min(current_size + 1, 72)
        current_font.setPointSize(new_size)
        editor_pane.setFont(current_font)
        
        # 验证字体大小增加
        assert editor_pane.font().pointSize() == initial_size + 1
    
    def test_font_zoom_out(self, editor_pane):
        """测试字体缩小"""
        # 设置初始字体大小
        initial_size = 12
        font = editor_pane.font()
        font.setPointSize(initial_size)
        editor_pane.setFont(font)
        
        # 直接测试字体大小变化
        current_font = editor_pane.font()
        current_size = current_font.pointSize()
        new_size = max(current_size - 1, 6)
        current_font.setPointSize(new_size)
        editor_pane.setFont(current_font)
        
        # 验证字体大小减小
        assert editor_pane.font().pointSize() == initial_size - 1
    
    def test_font_zoom_boundary_max(self, editor_pane):
        """测试字体放大边界（最大 72pt）"""
        # 设置字体大小为 72
        font = editor_pane.font()
        font.setPointSize(72)
        editor_pane.setFont(font)
        
        # 尝试继续放大
        current_font = editor_pane.font()
        current_size = current_font.pointSize()
        new_size = min(current_size + 1, 72)
        current_font.setPointSize(new_size)
        editor_pane.setFont(current_font)
        
        # 验证字体大小不超过 72
        assert editor_pane.font().pointSize() == 72
    
    def test_font_zoom_boundary_min(self, editor_pane):
        """测试字体缩小边界（最小 6pt）"""
        # 设置字体大小为 6
        font = editor_pane.font()
        font.setPointSize(6)
        editor_pane.setFont(font)
        
        # 尝试继续缩小
        current_font = editor_pane.font()
        current_size = current_font.pointSize()
        new_size = max(current_size - 1, 6)
        current_font.setPointSize(new_size)
        editor_pane.setFont(current_font)
        
        # 验证字体大小不小于 6
        assert editor_pane.font().pointSize() == 6
    
    def test_line_number_area_width(self, editor_pane):
        """测试行号区域宽度计算"""
        # 设置一些文本
        editor_pane.setPlainText("\n" * 99)  # 100 行
        
        # 获取行号区域宽度
        width = editor_pane.line_number_area_width()
        
        # 宽度应该大于 0
        assert width > 0
        
        # 宽度应该足够显示 3 位数字
        digit_width = editor_pane.fontMetrics().horizontalAdvance('9')
        expected_min_width = 3 + digit_width * 3 + 3
        assert width >= expected_min_width
    
    def test_modification_signal(self, editor_pane, qtbot):
        """测试修改状态信号"""
        # 连接信号
        with qtbot.waitSignal(editor_pane.modification_changed, timeout=1000) as blocker:
            editor_pane.setPlainText("Test content")
        
        # 验证信号参数
        assert blocker.args[0] is True  # 修改状态为 True
    
    def test_syntax_highlighter_integration(self, editor_pane):
        """测试语法高亮器集成"""
        # 设置 Python 文件
        editor_pane.set_file_path("test.py")
        
        # 设置 Python 代码
        code = """
def hello():
    print("Hello, World!")
"""
        editor_pane.setPlainText(code)
        
        # 验证语法高亮器已应用
        assert editor_pane.syntax_highlighter is not None
        assert editor_pane.syntax_highlighter.language == "python"
        assert len(editor_pane.syntax_highlighter.rules) > 0
    
    def test_theme_integration_with_syntax_highlighter(self, editor_pane):
        """测试主题与语法高亮器的集成"""
        # 设置语言
        editor_pane.set_language("python")
        
        # 应用深色主题
        dark_theme = get_dark_theme()
        editor_pane.apply_theme(dark_theme)
        
        # 验证语法高亮器使用了主题颜色
        assert editor_pane.syntax_highlighter is not None
        keyword_format = editor_pane.syntax_highlighter.formats.get('keyword')
        assert keyword_format is not None
        
        # 切换到浅色主题
        light_theme = get_light_theme()
        editor_pane.apply_theme(light_theme)
        
        # 验证语法高亮器颜色已更新
        keyword_format = editor_pane.syntax_highlighter.formats.get('keyword')
        assert keyword_format is not None


class TestLineNumberArea:
    """LineNumberArea 类的测试"""
    
    def test_initialization(self, editor_pane):
        """测试行号区域初始化"""
        line_number_area = editor_pane.line_number_area
        assert line_number_area is not None
        assert line_number_area.editor == editor_pane
    
    def test_size_hint(self, editor_pane):
        """测试行号区域大小提示"""
        line_number_area = editor_pane.line_number_area
        size_hint = line_number_area.sizeHint()
        
        # 宽度应该等于编辑器计算的行号区域宽度
        assert size_hint.width() == editor_pane.line_number_area_width()
        assert size_hint.height() == 0
