"""
编辑器窗格模块

该模块实现了单个文件的文本编辑区域，包含行号显示、语法高亮和主题支持。
"""

from typing import Optional, List
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import (
    QColor, QPainter, QTextFormat, QWheelEvent, QPaintEvent,
    QResizeEvent, QTextCursor, QFont, QKeyEvent, QMouseEvent
)

from core.syntax_highlighter import SyntaxHighlighter
from core.code_completer import CodeCompleter
from utils.language_detector import LanguageDetector
from themes.theme import Theme


class LineNumberArea(QWidget):
    """
    行号区域类
    
    显示编辑器的行号和代码折叠指示器。
    """
    
    def __init__(self, editor: 'EditorPane'):
        """
        初始化行号区域
        
        Args:
            editor: 关联的编辑器窗格
        """
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self) -> QSize:
        """
        返回建议大小
        
        Returns:
            QSize: 建议的大小
        """
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event: QPaintEvent):
        """
        绘制行号和折叠指示器
        
        Args:
            event: 绘制事件
        """
        self.editor.line_number_area_paint_event(event)


class EditorPane(QPlainTextEdit):
    """
    编辑器窗格类
    
    单个文件的文本编辑区域，支持行号显示、语法高亮、主题应用等功能。
    """
    
    # 信号：修改状态改变
    modification_changed = Signal(bool)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化编辑器窗格
        
        Args:
            parent: 父窗口部件
        """
        super().__init__(parent)
        
        # 文件路径
        self._file_path: Optional[str] = None
        
        # 语法高亮器
        self.syntax_highlighter: Optional[SyntaxHighlighter] = None
        
        # 行号区域
        self.line_number_area = LineNumberArea(self)
        
        # 多光标支持
        self.extra_cursors: List[QTextCursor] = []
        
        # 列选择支持
        self._column_selection_mode: bool = False
        self._column_selection_start: Optional[QTextCursor] = None
        self._column_selection_end: Optional[QTextCursor] = None
        
        # 代码补全器
        self.code_completer = CodeCompleter(self)
        
        # 双击高亮的单词
        self._highlighted_word: Optional[str] = None
        
        # 括号配对高亮的行号（可能有两个：当前行和配对行）
        self._bracket_match_lines: List[int] = []
        
        # 连接信号
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self._check_bracket_match)
        self.textChanged.connect(self._on_text_changed)
        
        # 初始化行号区域宽度
        self.update_line_number_area_width(0)
        
        # 禁用默认的拖放行为，让 MainWindow 处理文件拖放
        self.setAcceptDrops(False)
        
        # 高亮当前行
        self.highlight_current_line()
        
        # 设置默认字体
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.setFont(font)
        
        # 设置制表符宽度为 4 个空格
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
    
    def set_file_path(self, path: str) -> None:
        """
        设置关联的文件路径
        
        Args:
            path: 文件路径
        """
        self._file_path = path
        
        # 根据文件路径自动检测语言并设置语法高亮
        if path:
            language = LanguageDetector.detect_language(path)
            if language:
                self.set_language(language)
        else:
            # 无路径时，尝试基于内容检测
            self.trigger_content_detection()
    
    def get_file_path(self) -> Optional[str]:
        """
        获取文件路径
        
        Returns:
            Optional[str]: 文件路径，如果未设置则返回 None
        """
        return self._file_path
    
    def is_modified(self) -> bool:
        """
        检查是否已修改
        
        Returns:
            bool: 如果文档已修改返回 True，否则返回 False
        """
        return self.document().isModified()
    
    def set_language(self, language: str) -> None:
        """
        设置语法高亮语言
        
        Args:
            language: 语言名称（python, java, sql, json, javascript, kotlin）
        """
        if self.syntax_highlighter is None:
            # 创建新的语法高亮器
            self.syntax_highlighter = SyntaxHighlighter(self.document(), language)
            # 如果已经有主题，立即应用
            if hasattr(self, '_current_theme'):
                self.syntax_highlighter.apply_theme(self._current_theme)
        else:
            # 更新现有语法高亮器的语言
            self.syntax_highlighter.set_language(language)
        
        # 更新代码补全器的语言
        self.code_completer.set_language(language)
    
    def apply_theme(self, theme: Theme) -> None:
        """
        应用主题
        
        Args:
            theme: 主题对象
        """
        # 设置编辑器样式
        style_sheet = f"""
            QPlainTextEdit {{
                background-color: {theme.background};
                color: {theme.foreground};
                selection-background-color: {theme.selection_bg};
                selection-color: {theme.selection_fg};
                border: none;
            }}
        """
        self.setStyleSheet(style_sheet)
        
        # 应用主题到语法高亮器
        if self.syntax_highlighter:
            self.syntax_highlighter.apply_theme(theme)
        
        # 更新行号区域样式
        self.line_number_area.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.line_number_bg};
                color: {theme.line_number_fg};
            }}
        """)
        
        # 保存主题以便高亮当前行
        self._current_theme = theme
        
        # 重新高亮当前行
        self.highlight_current_line()
    
    def apply_zoom(self, zoom_level: int) -> None:
        """
        应用缩放级别
        
        Args:
            zoom_level: 缩放级别（0为默认，正数放大，负数缩小）
        """
        # 基础字体大小
        base_size = 10
        
        # 计算新的字体大小
        new_size = base_size + zoom_level
        
        # 限制在合理范围内
        new_size = max(6, min(72, new_size))
        
        # 应用新的字体大小
        font = self.font()
        font.setPointSize(new_size)
        self.setFont(font)
        
        # 更新制表符宽度
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        处理鼠标滚轮事件（用于缩放）
        
        Args:
            event: 滚轮事件
        """
        # 检查是否按下 Ctrl 键
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # 获取滚轮滚动方向
            delta = event.angleDelta().y()
            
            # 获取当前字体
            font = self.font()
            current_size = font.pointSize()
            
            # 计算新的字体大小
            if delta > 0:
                # 向上滚动，放大
                new_size = min(current_size + 1, 72)
            else:
                # 向下滚动，缩小
                new_size = max(current_size - 1, 6)
            
            # 应用新的字体大小
            if new_size != current_size:
                font.setPointSize(new_size)
                self.setFont(font)
                
                # 更新制表符宽度
                self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
            
            # 接受事件，防止传播
            event.accept()
        else:
            # 不是 Ctrl+滚轮，使用默认行为
            super().wheelEvent(event)
    
    def line_number_area_width(self) -> int:
        """
        计算行号区域的宽度
        
        Returns:
            int: 行号区域宽度（像素）
        """
        # 计算最大行号的位数
        digits = len(str(max(1, self.blockCount())))
        
        # 计算宽度：左边距 + 数字宽度 + 右边距
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits + 3
        
        return space
    
    def update_line_number_area_width(self, _: int):
        """
        更新行号区域宽度
        
        Args:
            _: 块数量（未使用）
        """
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect: QRect, dy: int):
        """
        更新行号区域
        
        Args:
            rect: 更新区域
            dy: 垂直滚动偏移
        """
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    
    def resizeEvent(self, event: QResizeEvent):
        """
        处理窗口大小改变事件
        
        Args:
            event: 大小改变事件
        """
        super().resizeEvent(event)
        
        # 更新行号区域的位置和大小
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
    
    def paintEvent(self, event: QPaintEvent):
        """
        处理绘制事件
        
        Args:
            event: 绘制事件
        """
        # 先调用父类的绘制方法
        super().paintEvent(event)
        
        # 如果处于列选择模式，绘制选择区域
        if self._column_selection_mode and self._column_selection_start and self._column_selection_end:
            self._draw_column_selection()
    
    def _draw_column_selection(self) -> None:
        """绘制列选择区域"""
        if not self._column_selection_start or not self._column_selection_end:
            return
        
        painter = QPainter(self.viewport())
        
        # 获取选择背景色
        if hasattr(self, '_current_theme'):
            selection_color = QColor(self._current_theme.selection_bg)
            selection_color.setAlpha(100)  # 半透明
        else:
            selection_color = QColor("#3d3d3d")
            selection_color.setAlpha(100)
        
        # 获取起始和结束位置
        start_block = self._column_selection_start.block().blockNumber()
        end_block = self._column_selection_end.block().blockNumber()
        start_column = self._column_selection_start.positionInBlock()
        end_column = self._column_selection_end.positionInBlock()
        
        # 确保起始行号小于结束行号
        if start_block > end_block:
            start_block, end_block = end_block, start_block
        
        # 确保起始列号小于结束列号
        if start_column > end_column:
            start_column, end_column = end_column, start_column
        
        # 为每一行绘制矩形
        for block_num in range(start_block, end_block + 1):
            block = self.document().findBlockByNumber(block_num)
            if not block.isValid():
                continue
            
            # 获取该行的文本
            block_text = block.text()
            block_length = len(block_text)
            
            # 计算该行的列范围（考虑行长度）
            line_start_col = min(start_column, block_length)
            line_end_col = min(end_column, block_length)
            
            # 创建光标来获取位置
            start_cursor = QTextCursor(block)
            start_cursor.setPosition(block.position() + line_start_col)
            end_cursor = QTextCursor(block)
            end_cursor.setPosition(block.position() + line_end_col)
            
            # 获取屏幕坐标
            start_rect = self.cursorRect(start_cursor)
            end_rect = self.cursorRect(end_cursor)
            
            # 绘制矩形
            if start_rect.isValid() and end_rect.isValid():
                rect = QRect(
                    start_rect.left(),
                    start_rect.top(),
                    end_rect.left() - start_rect.left(),
                    start_rect.height()
                )
                painter.fillRect(rect, selection_color)
    
    def line_number_area_paint_event(self, event: QPaintEvent):
        """
        绘制行号区域
        
        Args:
            event: 绘制事件
        """
        painter = QPainter(self.line_number_area)
        
        # 获取主题颜色（如果有）
        if hasattr(self, '_current_theme'):
            bg_color = QColor(self._current_theme.line_number_bg)
            fg_color = QColor(self._current_theme.line_number_fg)
            highlight_color = QColor(self._current_theme.selection_bg)
        else:
            bg_color = QColor("#2b2b2b")
            fg_color = QColor("#858585")
            highlight_color = QColor("#3d3d3d")
        
        # 填充背景
        painter.fillRect(event.rect(), bg_color)
        
        # 获取当前行号
        current_line = self.textCursor().blockNumber()
        
        # 获取第一个可见块
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        # 绘制行号
        painter.setPen(fg_color)
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                # 检查是否需要高亮（当前行或括号配对行）
                should_highlight = (block_number == current_line or 
                                  block_number in self._bracket_match_lines)
                
                if should_highlight:
                    # 绘制高亮背景
                    painter.fillRect(
                        0, top,
                        self.line_number_area.width(), self.fontMetrics().height(),
                        highlight_color
                    )
                    # 使用更亮的颜色绘制行号
                    painter.setPen(QColor("#FFFFFF"))
                    painter.drawText(
                        0, top,
                        self.line_number_area.width() - 3, self.fontMetrics().height(),
                        Qt.AlignmentFlag.AlignRight, number
                    )
                    painter.setPen(fg_color)
                else:
                    painter.drawText(
                        0, top,
                        self.line_number_area.width() - 3, self.fontMetrics().height(),
                        Qt.AlignmentFlag.AlignRight, number
                    )
            
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
    
    def highlight_current_line(self):
        """高亮当前行"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            
            # 获取当前行背景色
            if hasattr(self, '_current_theme'):
                line_color = QColor(self._current_theme.current_line_bg)
            else:
                line_color = QColor("#2f2f2f")
            
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        # 如果有高亮的单词，添加所有匹配项的高亮
        if self._highlighted_word:
            self._add_word_highlights(extra_selections)
        
        self.setExtraSelections(extra_selections)
    
    def _add_word_highlights(self, extra_selections: List) -> None:
        """
        添加单词高亮
        
        Args:
            extra_selections: 额外选择列表
        """
        if not self._highlighted_word:
            return
        
        # 获取高亮颜色
        if hasattr(self, '_current_theme'):
            highlight_color = QColor(self._current_theme.selection_bg)
            highlight_color.setAlpha(100)  # 半透明
        else:
            highlight_color = QColor("#3d3d3d")
        
        # 从文档开头开始查找所有匹配
        cursor = QTextCursor(self.document())
        cursor.setPosition(0)
        
        while True:
            cursor = self.document().find(self._highlighted_word, cursor)
            if cursor.isNull():
                break
            
            # 检查是否是完整的单词（不是单词的一部分）
            # 获取匹配前后的字符
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
            
            # 检查前一个字符
            if start_pos > 0:
                prev_cursor = QTextCursor(self.document())
                prev_cursor.setPosition(start_pos - 1)
                prev_cursor.setPosition(start_pos, QTextCursor.MoveMode.KeepAnchor)
                prev_char = prev_cursor.selectedText()
                if prev_char.isalnum() or prev_char == '_':
                    continue
            
            # 检查后一个字符
            if end_pos < self.document().characterCount() - 1:
                next_cursor = QTextCursor(self.document())
                next_cursor.setPosition(end_pos)
                next_cursor.setPosition(end_pos + 1, QTextCursor.MoveMode.KeepAnchor)
                next_char = next_cursor.selectedText()
                if next_char.isalnum() or next_char == '_':
                    continue
            
            # 添加高亮
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(highlight_color)
            selection.cursor = cursor
            extra_selections.append(selection)
    
    def _check_bracket_match(self) -> None:
        """检查括号配对并高亮配对括号所在行"""
        # 重置括号配对行号列表
        self._bracket_match_lines = []
        
        # 获取当前光标
        cursor = self.textCursor()
        pos = cursor.position()
        current_line = cursor.blockNumber()
        
        # 获取当前字符和前一个字符
        text = self.toPlainText()
        if not text or pos > len(text):
            self.line_number_area.update()
            return
        
        current_char = text[pos] if pos < len(text) else ''
        prev_char = text[pos - 1] if pos > 0 else ''
        
        # 定义括号对
        opening_brackets = '([{'
        closing_brackets = ')]}'
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        reverse_pairs = {v: k for k, v in bracket_pairs.items()}
        
        # 检查当前字符或前一个字符是否是括号
        check_char = None
        check_pos = None
        is_opening = False
        
        if current_char and current_char in opening_brackets:
            check_char = current_char
            check_pos = pos
            is_opening = True
        elif current_char and current_char in closing_brackets:
            check_char = current_char
            check_pos = pos
            is_opening = False
        elif prev_char and prev_char in opening_brackets:
            check_char = prev_char
            check_pos = pos - 1
            is_opening = True
        elif prev_char and prev_char in closing_brackets:
            check_char = prev_char
            check_pos = pos - 1
            is_opening = False
        
        if check_char is None or not check_char:
            self.line_number_area.update()
            return
        
        # 查找配对括号
        match_pos = self._find_matching_bracket(text, check_pos, check_char, is_opening)
        
        if match_pos is not None:
            # 获取配对括号所在的行号
            match_cursor = QTextCursor(self.document())
            match_cursor.setPosition(match_pos)
            match_line = match_cursor.blockNumber()
            
            # 添加配对括号所在行到高亮列表
            self._bracket_match_lines.append(match_line)
            
            # 如果配对括号不在当前行，也添加当前行（这样两行都会高亮）
            # 注意：当前行已经在 line_number_area_paint_event 中通过 current_line 高亮了
            
            # 更新行号区域显示
            self.line_number_area.update()
    
    def _find_matching_bracket(self, text: str, pos: int, bracket: str, is_opening: bool) -> Optional[int]:
        """
        查找配对的括号
        
        Args:
            text: 文本内容
            pos: 当前括号位置
            bracket: 当前括号字符
            is_opening: 是否是开括号
            
        Returns:
            Optional[int]: 配对括号的位置，如果没找到返回 None
        """
        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        reverse_pairs = {v: k for k, v in bracket_pairs.items()}
        
        if is_opening:
            # 向后查找闭括号
            target = bracket_pairs[bracket]
            direction = 1
            start = pos + 1
            end = len(text)
        else:
            # 向前查找开括号
            target = reverse_pairs[bracket]
            direction = -1
            start = pos - 1
            end = -1
        
        count = 1
        i = start
        
        while (direction > 0 and i < end) or (direction < 0 and i > end):
            char = text[i]
            
            if char == bracket:
                count += 1
            elif char == target:
                count -= 1
                if count == 0:
                    return i
            
            i += direction
        
        return None
    
    def add_cursor_at_position(self, position: int) -> None:
        """
        在指定位置添加光标
        
        Args:
            position: 文本位置
        """
        # 创建新光标
        cursor = QTextCursor(self.document())
        cursor.setPosition(position)
        
        # 检查是否已经存在相同位置的光标
        main_cursor = self.textCursor()
        if main_cursor.position() == position:
            return
        
        for existing_cursor in self.extra_cursors:
            if existing_cursor.position() == position:
                return
        
        # 添加到额外光标列表
        self.extra_cursors.append(cursor)
        
        # 更新显示
        self._update_cursor_display()
    
    def clear_extra_cursors(self) -> None:
        """清除所有额外光标，仅保留主光标"""
        self.extra_cursors.clear()
        self._update_cursor_display()
    
    def _update_cursor_display(self) -> None:
        """更新光标显示"""
        extra_selections = []
        
        # 添加当前行高亮
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            
            # 获取当前行背景色
            if hasattr(self, '_current_theme'):
                line_color = QColor(self._current_theme.current_line_bg)
            else:
                line_color = QColor("#2f2f2f")
            
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()  # 只清除用于显示的副本，不影响实际光标
            extra_selections.append(selection)
        
        # 添加额外光标的显示
        for cursor in self.extra_cursors:
            selection = QTextEdit.ExtraSelection()
            
            # 使用选择背景色来显示额外光标
            if hasattr(self, '_current_theme'):
                cursor_color = QColor(self._current_theme.selection_bg)
            else:
                cursor_color = QColor("#3d3d3d")
            
            selection.format.setBackground(cursor_color)
            # 创建光标的副本用于显示，不修改原始光标
            display_cursor = QTextCursor(cursor)
            selection.cursor = display_cursor
            # 如果光标没有选择，选择当前字符以显示光标位置
            if not display_cursor.hasSelection():
                display_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        处理鼠标按下事件
        
        Args:
            event: 鼠标事件
        """
        # 检查是否按下鼠标中键（列选择模式）
        if event.button() == Qt.MouseButton.MiddleButton:
            # 进入列选择模式
            cursor = self.cursorForPosition(event.pos())
            self._column_selection_mode = True
            self._column_selection_start = QTextCursor(cursor)
            self._column_selection_end = QTextCursor(cursor)
            
            # 清除现有的额外光标
            self.clear_extra_cursors()
            
            # 接受事件
            event.accept()
            return
        
        # 检查是否按下 Ctrl 键
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # 获取点击位置的光标
            cursor = self.cursorForPosition(event.pos())
            position = cursor.position()
            
            # 添加光标
            self.add_cursor_at_position(position)
            
            # 接受事件
            event.accept()
        else:
            # 清除额外光标和列选择模式
            if self.extra_cursors:
                self.clear_extra_cursors()
            if self._column_selection_mode:
                self._column_selection_mode = False
                self._column_selection_start = None
                self._column_selection_end = None
                self.viewport().update()
            
            # 使用默认行为
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        处理鼠标移动事件
        
        Args:
            event: 鼠标事件
        """
        # 如果处于列选择模式，更新选择区域
        if self._column_selection_mode:
            cursor = self.cursorForPosition(event.pos())
            self._column_selection_end = QTextCursor(cursor)
            
            # 触发重绘以显示选择区域
            self.viewport().update()
            
            # 接受事件
            event.accept()
            return
        
        # 使用默认行为
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        处理鼠标释放事件
        
        Args:
            event: 鼠标事件
        """
        # 如果是鼠标中键释放，完成列选择
        if event.button() == Qt.MouseButton.MiddleButton and self._column_selection_mode:
            # 从列选择区域创建多光标
            self._create_cursors_from_column_selection()
            
            # 退出列选择模式
            self._column_selection_mode = False
            self._column_selection_start = None
            self._column_selection_end = None
            
            # 更新显示
            self.viewport().update()
            
            # 接受事件
            event.accept()
            return
        
        # 使用默认行为
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """
        处理鼠标双击事件
        
        Args:
            event: 鼠标事件
        """
        # 使用默认行为选择单词
        super().mouseDoubleClickEvent(event)
        
        # 获取选中的单词
        cursor = self.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text and (selected_text[0].isalnum() or selected_text[0] == '_'):
            # 保存高亮的单词
            self._highlighted_word = selected_text
            # 更新高亮显示
            self.highlight_current_line()
        else:
            # 清除高亮
            self._highlighted_word = None
            self.highlight_current_line()
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        处理键盘按下事件
        
        Args:
            event: 键盘事件
        """
        # 如果补全弹窗可见，处理补全相关的按键
        if self.code_completer.popup().isVisible():
            # 这些键由补全器处理
            if event.key() in (
                Qt.Key.Key_Enter, Qt.Key.Key_Return,
                Qt.Key.Key_Escape, Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab
            ):
                event.ignore()
                return
        
        # 处理 Escape 键
        if event.key() == Qt.Key.Key_Escape:
            # 清除列选择模式
            if self._column_selection_mode:
                self._column_selection_mode = False
                self._column_selection_start = None
                self._column_selection_end = None
                self.viewport().update()
                event.accept()
                return
            
            # 清除额外光标
            if self.extra_cursors:
                self.clear_extra_cursors()
                event.accept()
                return
        
        # 处理 Ctrl+D
        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._select_next_occurrence()
            event.accept()
            return
        
        # 如果有额外光标，同步操作
        if self.extra_cursors:
            # 处理删除键 - 必须在文本输入之前检查！
            if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
                self._multi_cursor_delete(event.key() == Qt.Key.Key_Backspace)
                event.accept()
                return
            
            # 处理文本输入
            if event.text() and not event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
                self._multi_cursor_insert(event.text())
                event.accept()
                return
        
        # 使用默认行为
        super().keyPressEvent(event)
        
        # 触发代码补全
        # 检查是否应该显示补全
        if event.text() and event.text().isalnum() or event.text() == '_':
            # 获取光标下的文本
            prefix = self.code_completer.text_under_cursor()
            if len(prefix) >= 2:
                self.code_completer.update_completions(prefix)
    
    def _multi_cursor_insert(self, text: str) -> None:
        """
        在所有光标位置插入文本
        
        Args:
            text: 要插入的文本
        """
        # 获取主光标
        main_cursor = self.textCursor()
        
        # 收集所有光标（包括主光标）
        all_cursors = [main_cursor] + self.extra_cursors
        
        # 按位置排序（从后往前，避免位置偏移）
        all_cursors.sort(key=lambda c: c.position(), reverse=True)
        
        # 在所有光标位置插入文本
        for cursor in all_cursors:
            cursor.insertText(text)
        
        # 更新主光标
        self.setTextCursor(main_cursor)
        
        # 更新显示
        self._update_cursor_display()
    
    def _multi_cursor_delete(self, backspace: bool = True) -> None:
        """
        在所有光标位置删除文本
        
        Args:
            backspace: True 表示删除前一个字符，False 表示删除后一个字符
        """
        # 获取主光标
        main_cursor = self.textCursor()
        
        # 收集所有光标（包括主光标）
        all_cursors = [main_cursor] + self.extra_cursors
        
        # 按位置排序（从后往前，避免位置偏移）
        all_cursors.sort(key=lambda c: c.position(), reverse=True)
        
        # 开始编辑事务（支持撤销）
        main_cursor.beginEditBlock()
        
        try:
            # 从后往前删除，避免位置偏移
            for cursor in all_cursors:
                if cursor.hasSelection():
                    # 如果有选择，删除选中的文本
                    cursor.removeSelectedText()
                else:
                    # 如果没有选择，删除前一个或后一个字符
                    if backspace:
                        cursor.deletePreviousChar()
                    else:
                        cursor.deleteChar()
        finally:
            # 结束编辑事务
            main_cursor.endEditBlock()
        
        # 更新主光标（使用第一个光标的位置）
        all_cursors.sort(key=lambda c: c.position())
        if all_cursors:
            self.setTextCursor(all_cursors[0])
        
        # 清除额外光标
        self.extra_cursors.clear()
        
        # 更新显示
        self._update_cursor_display()
    
    def _select_next_occurrence(self) -> None:
        """选择下一个相同文本并添加光标"""
        # 获取当前选中的文本
        main_cursor = self.textCursor()
        selected_text = main_cursor.selectedText()
        
        # 如果没有选中文本，选择当前单词
        if not selected_text:
            main_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            selected_text = main_cursor.selectedText()
            self.setTextCursor(main_cursor)
        
        if not selected_text:
            return
        
        # 从当前位置开始查找下一个匹配
        search_cursor = QTextCursor(self.document())
        search_cursor.setPosition(main_cursor.selectionEnd())
        
        # 查找下一个匹配
        found_cursor = self.document().find(selected_text, search_cursor)
        
        # 如果没找到，从文档开头重新查找
        if found_cursor.isNull():
            search_cursor.setPosition(0)
            found_cursor = self.document().find(selected_text, search_cursor)
        
        # 如果找到了，添加光标
        if not found_cursor.isNull():
            # 检查是否已经是主光标或额外光标的位置
            if found_cursor.position() != main_cursor.position():
                is_duplicate = False
                for cursor in self.extra_cursors:
                    if cursor.position() == found_cursor.position():
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    self.extra_cursors.append(found_cursor)
                    self._update_cursor_display()
    
    def _on_text_changed(self):
        """文本改变时的处理"""
        # 发射修改状态改变信号
        self.modification_changed.emit(self.is_modified())
    
    def trigger_content_detection(self) -> None:
        """
        触发基于内容的语言检测
        当用户粘贴内容到新文档时调用
        """
        if not self._file_path:  # 只在无文件路径时检测
            content = self.toPlainText()
            if content.strip():
                language = LanguageDetector.detect_language_from_content(content)
                if language:
                    self.set_language(language)
    
    def _create_cursors_from_column_selection(self) -> None:
        """从列选择区域创建多光标"""
        if not self._column_selection_start or not self._column_selection_end:
            return
        
        # 获取起始和结束位置
        start_block = self._column_selection_start.block().blockNumber()
        end_block = self._column_selection_end.block().blockNumber()
        start_column = self._column_selection_start.positionInBlock()
        end_column = self._column_selection_end.positionInBlock()
        
        # 确保起始行号小于结束行号
        if start_block > end_block:
            start_block, end_block = end_block, start_block
        
        # 如果只有一行，不创建列选择
        if start_block == end_block:
            return
        
        # 清除现有的额外光标
        self.extra_cursors.clear()
        
        # 为每一行创建光标
        # 注意：对于竖向拖动（start_column == end_column），我们不设置选择，只设置光标位置
        for block_num in range(start_block, end_block + 1):
            block = self.document().findBlockByNumber(block_num)
            if not block.isValid():
                continue
            
            # 获取该行的文本
            block_text = block.text()
            block_length = len(block_text)
            
            # 计算该行的列位置（考虑行长度）
            # 对于竖向拖动，使用较小的列号
            column = min(min(start_column, end_column), block_length)
            
            # 创建光标并设置位置
            cursor = QTextCursor(block)
            cursor.setPosition(block.position() + column)
            
            # 如果是矩形选择（start_column != end_column），设置选择范围
            if start_column != end_column:
                line_end_col = min(max(start_column, end_column), block_length)
                cursor.setPosition(block.position() + line_end_col, QTextCursor.MoveMode.KeepAnchor)
            
            # 第一行作为主光标，其他行作为额外光标
            if block_num == start_block:
                self.setTextCursor(cursor)
            else:
                self.extra_cursors.append(cursor)
        
        # 更新显示
        self._update_cursor_display()
