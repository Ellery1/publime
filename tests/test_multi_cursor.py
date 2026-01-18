"""
多光标编辑测试模块

测试编辑器窗格的多光标编辑功能。
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from ui.editor_pane import EditorPane


@pytest.fixture
def app(qapp):
    """Qt 应用程序 fixture"""
    return qapp


@pytest.fixture
def editor(app):
    """编辑器窗格 fixture"""
    editor = EditorPane()
    return editor


def test_add_cursor_at_position(editor):
    """测试在指定位置添加光标"""
    # 设置初始文本
    editor.setPlainText("line 1\nline 2\nline 3")
    
    # 添加光标
    editor.add_cursor_at_position(7)  # line 2 的开头
    
    # 验证额外光标数量
    assert len(editor.extra_cursors) == 1
    assert editor.extra_cursors[0].position() == 7


def test_add_multiple_cursors(editor):
    """测试添加多个光标"""
    # 设置初始文本
    editor.setPlainText("line 1\nline 2\nline 3")
    
    # 添加多个光标
    editor.add_cursor_at_position(7)   # line 2 的开头
    editor.add_cursor_at_position(14)  # line 3 的开头
    
    # 验证额外光标数量
    assert len(editor.extra_cursors) == 2


def test_add_duplicate_cursor_ignored(editor):
    """测试添加重复位置的光标会被忽略"""
    # 设置初始文本
    editor.setPlainText("line 1\nline 2\nline 3")
    
    # 添加光标
    editor.add_cursor_at_position(7)
    editor.add_cursor_at_position(7)  # 重复位置
    
    # 验证只有一个额外光标
    assert len(editor.extra_cursors) == 1


def test_clear_extra_cursors(editor):
    """测试清除额外光标"""
    # 设置初始文本
    editor.setPlainText("line 1\nline 2\nline 3")
    
    # 添加多个光标
    editor.add_cursor_at_position(7)
    editor.add_cursor_at_position(14)
    
    # 清除额外光标
    editor.clear_extra_cursors()
    
    # 验证额外光标已清除
    assert len(editor.extra_cursors) == 0


def test_multi_cursor_insert(editor):
    """测试多光标同步插入文本"""
    # 设置初始文本
    editor.setPlainText("abc\nabc\nabc")
    
    # 设置主光标在第一行开头
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    # 添加额外光标
    editor.add_cursor_at_position(4)   # 第二行开头
    editor.add_cursor_at_position(8)   # 第三行开头
    
    # 插入文本
    editor._multi_cursor_insert("X")
    
    # 验证所有位置都插入了文本
    expected = "Xabc\nXabc\nXabc"
    assert editor.toPlainText() == expected


def test_multi_cursor_delete_backspace(editor):
    """测试多光标同步删除（Backspace）"""
    # 设置初始文本
    editor.setPlainText("Xabc\nXabc\nXabc")
    
    # 设置主光标在第一行 X 后面
    cursor = editor.textCursor()
    cursor.setPosition(1)
    editor.setTextCursor(cursor)
    
    # 添加额外光标
    editor.add_cursor_at_position(6)   # 第二行 X 后面
    editor.add_cursor_at_position(11)  # 第三行 X 后面
    
    # 删除前一个字符
    editor._multi_cursor_delete(backspace=True)
    
    # 验证所有位置都删除了字符
    expected = "abc\nabc\nabc"
    assert editor.toPlainText() == expected


def test_multi_cursor_delete_forward(editor):
    """测试多光标同步删除（Delete）"""
    # 设置初始文本
    editor.setPlainText("Xabc\nXabc\nXabc")
    
    # 设置主光标在第一行开头
    cursor = editor.textCursor()
    cursor.setPosition(0)
    editor.setTextCursor(cursor)
    
    # 添加额外光标
    editor.add_cursor_at_position(5)   # 第二行开头
    editor.add_cursor_at_position(10)  # 第三行开头
    
    # 删除后一个字符
    editor._multi_cursor_delete(backspace=False)
    
    # 验证所有位置都删除了字符
    expected = "abc\nabc\nabc"
    assert editor.toPlainText() == expected


def test_select_next_occurrence(editor):
    """测试选择下一个相同文本"""
    # 设置初始文本
    editor.setPlainText("foo bar foo baz foo")
    
    # 选择第一个 "foo"
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    
    # 选择下一个 "foo"
    editor._select_next_occurrence()
    
    # 验证添加了一个额外光标
    assert len(editor.extra_cursors) == 1
    
    # 验证额外光标选中了 "foo"
    extra_cursor = editor.extra_cursors[0]
    assert extra_cursor.selectedText() == "foo"
    assert extra_cursor.selectionStart() == 8  # "foo bar foo" 中第二个 foo 的位置


def test_select_next_occurrence_wraps_around(editor):
    """测试选择下一个相同文本时循环到开头"""
    # 设置初始文本
    editor.setPlainText("foo bar foo")
    
    # 选择第二个 "foo"
    cursor = editor.textCursor()
    cursor.setPosition(8)
    cursor.setPosition(11, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    
    # 选择下一个 "foo"（应该循环到第一个）
    editor._select_next_occurrence()
    
    # 验证添加了一个额外光标
    assert len(editor.extra_cursors) == 1
    
    # 验证额外光标选中了第一个 "foo"
    extra_cursor = editor.extra_cursors[0]
    assert extra_cursor.selectedText() == "foo"
    assert extra_cursor.selectionStart() == 0


def test_select_next_occurrence_no_duplicates(editor):
    """测试选择下一个相同文本时不会添加重复光标"""
    # 设置初始文本
    editor.setPlainText("foo bar foo")
    
    # 选择第一个 "foo"
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    
    # 第一次选择下一个
    editor._select_next_occurrence()
    assert len(editor.extra_cursors) == 1
    
    # 第二次选择下一个（应该循环到第一个，但不添加重复）
    editor._select_next_occurrence()
    # 由于第一个 foo 是主光标位置，不应该添加
    assert len(editor.extra_cursors) == 1
