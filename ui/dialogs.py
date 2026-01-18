"""
对话框模块

提供查找/替换对话框和跨文件搜索对话框。
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QTextEdit, QFileDialog, QListWidget,
    QListWidgetItem, QGroupBox, QMessageBox, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor
from core.search_engine import SearchEngine, Match
from typing import Optional, List


class FindDialog(QDialog):
    """查找/替换对话框"""
    
    # 信号
    find_next = Signal()
    find_previous = Signal()
    replace_current = Signal()
    replace_all = Signal()
    
    def __init__(self, parent=None):
        """初始化查找对话框"""
        super().__init__(parent)
        self.search_engine = SearchEngine()
        self.current_editor = None
        self.matches = []
        self.current_match_index = -1
        
        self.setup_ui()
        self.setWindowTitle("查找和替换")
        self.resize(500, 200)
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        
        # 查找输入
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        self.find_input.textChanged.connect(self.on_find_text_changed)
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)
        
        # 替换输入
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("替换:"))
        self.replace_input = QLineEdit()
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)
        
        # 选项 - 第一行
        options_layout1 = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("区分大小写")
        self.case_sensitive_cb.toggled.connect(self.on_option_changed)  # 添加信号连接
        self.regex_cb = QCheckBox("正则表达式")
        self.regex_cb.toggled.connect(self.on_option_changed)  # 添加信号连接
        options_layout1.addWidget(self.case_sensitive_cb)
        options_layout1.addWidget(self.regex_cb)
        options_layout1.addStretch()
        layout.addLayout(options_layout1)
        
        # 选项 - 第二行（匹配模式）
        options_layout2 = QHBoxLayout()
        options_layout2.addWidget(QLabel("匹配模式:"))
        
        # 创建互斥的单选按钮组
        self.match_mode_group = QButtonGroup(self)
        
        self.fuzzy_match_rb = QRadioButton("模糊匹配")
        self.fuzzy_match_rb.setChecked(True)  # 默认模糊匹配
        self.fuzzy_match_rb.toggled.connect(self.on_match_mode_changed)
        self.match_mode_group.addButton(self.fuzzy_match_rb)
        options_layout2.addWidget(self.fuzzy_match_rb)
        
        self.exact_match_rb = QRadioButton("精确匹配")
        self.exact_match_rb.toggled.connect(self.on_match_mode_changed)
        self.match_mode_group.addButton(self.exact_match_rb)
        options_layout2.addWidget(self.exact_match_rb)
        
        options_layout2.addStretch()
        layout.addLayout(options_layout2)
        
        # 匹配计数标签
        self.match_count_label = QLabel("匹配: 0")
        layout.addWidget(self.match_count_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.find_next_btn = QPushButton("查找下一个")
        self.find_next_btn.clicked.connect(self.on_find_next)
        button_layout.addWidget(self.find_next_btn)
        
        self.find_prev_btn = QPushButton("查找上一个")
        self.find_prev_btn.clicked.connect(self.on_find_previous)
        button_layout.addWidget(self.find_prev_btn)
        
        self.replace_btn = QPushButton("替换")
        self.replace_btn.clicked.connect(self.on_replace_current)
        button_layout.addWidget(self.replace_btn)
        
        self.replace_all_btn = QPushButton("全部替换")
        self.replace_all_btn.clicked.connect(self.on_replace_all)
        button_layout.addWidget(self.replace_all_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def set_editor(self, editor):
        """设置当前编辑器"""
        self.current_editor = editor
        self.update_search()
    
    def on_match_mode_changed(self):
        """匹配模式改变时"""
        self.update_search()
    
    def on_option_changed(self):
        """选项改变时（区分大小写、正则表达式）"""
        self.update_search()
    
    def on_find_text_changed(self):
        """查找文本改变时"""
        self.update_search()
    
    def update_search(self):
        """更新搜索结果"""
        if not self.current_editor:
            return
        
        pattern = self.find_input.text()
        if not pattern:
            self.matches = []
            self.current_match_index = -1
            self.match_count_label.setText("匹配: 0")
            self.clear_highlights()
            return
        
        # 获取编辑器文本
        text = self.current_editor.toPlainText()
        
        # 判断是否精确匹配
        is_exact_match = self.exact_match_rb.isChecked()
        
        # 执行搜索
        try:
            if is_exact_match:
                # 精确匹配：使用正则表达式的单词边界
                import re
                # 转义特殊字符
                escaped_pattern = re.escape(pattern)
                # 添加单词边界
                regex_pattern = r'\b' + escaped_pattern + r'\b'
                self.matches = self.search_engine.find_in_text(
                    text,
                    regex_pattern,
                    case_sensitive=self.case_sensitive_cb.isChecked(),
                    regex=True  # 精确匹配使用正则表达式
                )
            else:
                # 模糊匹配：正常搜索
                self.matches = self.search_engine.find_in_text(
                    text,
                    pattern,
                    case_sensitive=self.case_sensitive_cb.isChecked(),
                    regex=self.regex_cb.isChecked()
                )
            
            # 更新匹配计数
            count = len(self.matches)
            if count > 0 and self.current_match_index >= 0:
                self.match_count_label.setText(
                    f"匹配: {self.current_match_index + 1}/{count}"
                )
            else:
                self.match_count_label.setText(f"匹配: {count}")
            
            # 高亮所有匹配项
            self.highlight_all_matches()
            
            # 如果有匹配项，跳转到第一个
            if count > 0:
                self.current_match_index = 0
                self.jump_to_match(0)
        
        except ValueError as e:
            # 正则表达式错误
            self.match_count_label.setText(f"错误: {str(e)}")
            self.matches = []
            self.current_match_index = -1
    
    def highlight_all_matches(self):
        """高亮所有匹配项"""
        if not self.current_editor:
            return
        
        # 清除之前的高亮
        self.clear_highlights()
        
        # 创建高亮格式
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(255, 255, 0, 100))  # 黄色半透明
        
        # 高亮每个匹配项
        cursor = self.current_editor.textCursor()
        for match in self.matches:
            cursor.setPosition(match.start_pos)
            cursor.setPosition(match.end_pos, QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(highlight_format)
    
    def clear_highlights(self):
        """清除高亮"""
        if not self.current_editor:
            return
        
        cursor = self.current_editor.textCursor()
        cursor.select(QTextCursor.Document)
        
        # 重置格式
        format = QTextCharFormat()
        cursor.setCharFormat(format)
        
        # 恢复光标位置
        cursor.clearSelection()
        self.current_editor.setTextCursor(cursor)
    
    def jump_to_match(self, index: int):
        """跳转到指定匹配项"""
        if not self.current_editor or not self.matches:
            return
        
        if 0 <= index < len(self.matches):
            match = self.matches[index]
            cursor = self.current_editor.textCursor()
            cursor.setPosition(match.start_pos)
            cursor.setPosition(match.end_pos, QTextCursor.KeepAnchor)
            self.current_editor.setTextCursor(cursor)
            self.current_editor.ensureCursorVisible()
            
            self.current_match_index = index
            self.match_count_label.setText(
                f"匹配: {index + 1}/{len(self.matches)}"
            )
    
    def on_find_next(self):
        """查找下一个"""
        if not self.matches:
            return
        
        next_index = (self.current_match_index + 1) % len(self.matches)
        self.jump_to_match(next_index)
    
    def on_find_previous(self):
        """查找上一个"""
        if not self.matches:
            return
        
        prev_index = (self.current_match_index - 1) % len(self.matches)
        self.jump_to_match(prev_index)
    
    def on_replace_current(self):
        """替换当前匹配项"""
        if not self.current_editor or not self.matches:
            return
        
        if self.current_match_index < 0 or self.current_match_index >= len(self.matches):
            return
        
        # 获取当前匹配项
        match = self.matches[self.current_match_index]
        replacement = self.replace_input.text()
        
        # 替换文本
        cursor = self.current_editor.textCursor()
        cursor.setPosition(match.start_pos)
        cursor.setPosition(match.end_pos, QTextCursor.KeepAnchor)
        cursor.insertText(replacement)
        
        # 更新搜索（因为文本已改变）
        self.update_search()
    
    def on_replace_all(self):
        """全部替换"""
        if not self.current_editor:
            return
        
        pattern = self.find_input.text()
        replacement = self.replace_input.text()
        
        if not pattern:
            return
        
        # 获取编辑器文本
        text = self.current_editor.toPlainText()
        
        # 执行替换
        try:
            new_text, count = self.search_engine.replace_in_text(
                text,
                pattern,
                replacement,
                case_sensitive=self.case_sensitive_cb.isChecked(),
                regex=self.regex_cb.isChecked(),
                replace_all=True
            )
            
            # 更新编辑器文本
            self.current_editor.setPlainText(new_text)
            
            # 显示替换结果
            QMessageBox.information(
                self,
                "替换完成",
                f"已替换 {count} 处"
            )
            
            # 更新搜索
            self.update_search()
        
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
    
    def showEvent(self, event):
        """对话框显示时"""
        super().showEvent(event)
        self.find_input.setFocus()
        self.find_input.selectAll()


class FindInFilesDialog(QDialog):
    """跨文件搜索对话框"""
    
    # 信号：当用户点击搜索结果时发出 (file_path, line_number, column)
    result_clicked = Signal(str, int, int)
    
    def __init__(self, parent=None):
        """初始化跨文件搜索对话框"""
        super().__init__(parent)
        self.search_engine = SearchEngine()
        self.search_results = {}
        self.file_name_results = []  # 文件名搜索结果
        
        self.setup_ui()
        self.setWindowTitle("在文件中查找")
        self.resize(700, 550)
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        
        # 搜索输入组
        search_group = QGroupBox("搜索")
        search_layout = QVBoxLayout()
        
        # 查找输入
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        find_layout.addWidget(self.find_input)
        search_layout.addLayout(find_layout)
        
        # 目录选择
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("目录:"))
        self.dir_input = QLineEdit()
        dir_layout.addWidget(self.dir_input)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.on_browse_directory)
        dir_layout.addWidget(self.browse_btn)
        search_layout.addLayout(dir_layout)
        
        # 文件类型过滤
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("文件类型:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("例如: *.py, *.txt (留空搜索所有文件)")
        filter_layout.addWidget(self.filter_input)
        search_layout.addLayout(filter_layout)
        
        # 搜索模式选项（第一行）
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("搜索模式:"))
        self.search_content_cb = QCheckBox("搜索文件内容")
        self.search_content_cb.setChecked(True)  # 默认搜索内容
        self.search_filename_cb = QCheckBox("搜索文件名")
        mode_layout.addWidget(self.search_content_cb)
        mode_layout.addWidget(self.search_filename_cb)
        mode_layout.addStretch()
        search_layout.addLayout(mode_layout)
        
        # 匹配选项（第二行）
        match_layout = QHBoxLayout()
        match_layout.addWidget(QLabel("匹配选项:"))
        self.fuzzy_match_cb = QCheckBox("模糊匹配")
        self.fuzzy_match_cb.setChecked(True)  # 默认模糊匹配
        self.exact_match_cb = QCheckBox("精确匹配")
        self.case_sensitive_cb = QCheckBox("区分大小写")
        self.regex_cb = QCheckBox("正则表达式")
        match_layout.addWidget(self.fuzzy_match_cb)
        match_layout.addWidget(self.exact_match_cb)
        match_layout.addWidget(self.case_sensitive_cb)
        match_layout.addWidget(self.regex_cb)
        match_layout.addStretch()
        search_layout.addLayout(match_layout)
        
        # 连接互斥选项
        self.fuzzy_match_cb.toggled.connect(self.on_fuzzy_toggled)
        self.exact_match_cb.toggled.connect(self.on_exact_toggled)
        
        # 搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_btn)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # 结果列表
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout()
        
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        results_layout.addWidget(self.results_list)
        
        self.result_count_label = QLabel("结果: 0")
        results_layout.addWidget(self.result_count_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.setLayout(layout)
    
    def on_browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择搜索目录",
            self.dir_input.text()
        )
        
        if directory:
            self.dir_input.setText(directory)
    
    def on_fuzzy_toggled(self, checked):
        """模糊匹配切换"""
        if checked:
            self.exact_match_cb.setChecked(False)
    
    def on_exact_toggled(self, checked):
        """精确匹配切换"""
        if checked:
            self.fuzzy_match_cb.setChecked(False)
    
    def on_search(self):
        """执行搜索"""
        pattern = self.find_input.text()
        directory = self.dir_input.text()
        
        if not pattern:
            QMessageBox.warning(self, "警告", "请输入搜索内容")
            return
        
        if not directory:
            QMessageBox.warning(self, "警告", "请选择搜索目录")
            return
        
        # 验证目录是否存在
        import os
        if not os.path.exists(directory):
            QMessageBox.warning(self, "目录不存在", f"目录不存在: {directory}")
            return
        
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "无效目录", f"不是有效的目录: {directory}")
            return
        
        # 检查是否至少选择了一种搜索模式
        search_content = self.search_content_cb.isChecked()
        search_filename = self.search_filename_cb.isChecked()
        
        if not search_content and not search_filename:
            QMessageBox.warning(self, "警告", "请至少选择一种搜索模式（文件内容或文件名）")
            return
        
        # 解析文件类型过滤器
        filter_text = self.filter_input.text().strip()
        file_patterns = None
        if filter_text:
            file_patterns = [p.strip() for p in filter_text.split(',')]
        
        # 确定匹配模式
        is_fuzzy = self.fuzzy_match_cb.isChecked()
        is_exact = self.exact_match_cb.isChecked()
        
        # 如果两个都没选，默认使用模糊匹配
        if not is_fuzzy and not is_exact:
            is_fuzzy = True
        
        # 执行搜索
        try:
            # 清空之前的结果
            self.search_results = {}
            self.file_name_results = []
            self.results_list.clear()
            self.result_count_label.setText("正在搜索中，请稍等...")
            
            # 禁用搜索按钮
            self.search_btn.setEnabled(False)
            self.search_btn.setText("搜索中...")
            
            # 强制刷新界面
            QApplication.processEvents()
            
            # 搜索文件内容
            if search_content:
                self.search_results = self.search_engine.find_in_files(
                    directory,
                    pattern,
                    file_patterns=file_patterns,
                    case_sensitive=self.case_sensitive_cb.isChecked(),
                    regex=self.regex_cb.isChecked()
                )
            
            # 搜索文件名
            if search_filename:
                self.file_name_results = self.search_file_names(
                    directory,
                    pattern,
                    file_patterns=file_patterns,
                    case_sensitive=self.case_sensitive_cb.isChecked(),
                    exact_match=is_exact
                )
            
            # 显示结果
            self.display_results()
        
        except ValueError as e:
            # 无效的正则表达式
            self.results_list.clear()
            self.result_count_label.setText("搜索失败")
            QMessageBox.warning(self, "正则表达式错误", f"无效的正则表达式: {str(e)}")
        except PermissionError as e:
            self.results_list.clear()
            self.result_count_label.setText("搜索失败")
            QMessageBox.warning(self, "权限不足", f"没有访问权限: {str(e)}")
        except Exception as e:
            self.results_list.clear()
            self.result_count_label.setText("搜索失败")
            QMessageBox.warning(self, "搜索错误", f"搜索时发生错误: {str(e)}")
        
        finally:
            self.search_btn.setEnabled(True)
            self.search_btn.setText("搜索")
    
    def search_file_names(self, directory: str, pattern: str, file_patterns=None, 
                          case_sensitive=False, exact_match=False) -> List[str]:
        """
        搜索文件名
        
        Args:
            directory: 搜索目录
            pattern: 搜索模式
            file_patterns: 文件类型过滤器
            case_sensitive: 是否区分大小写
            exact_match: 是否精确匹配
        
        Returns:
            匹配的文件路径列表
        """
        import os
        import fnmatch
        
        results = []
        
        # 准备搜索模式
        search_pattern = pattern if case_sensitive else pattern.lower()
        
        # 遍历目录
        for root, dirs, files in os.walk(directory):
            for filename in files:
                # 应用文件类型过滤
                if file_patterns:
                    match_filter = False
                    for fp in file_patterns:
                        if fnmatch.fnmatch(filename, fp):
                            match_filter = True
                            break
                    if not match_filter:
                        continue
                
                # 准备文件名用于比较
                compare_name = filename if case_sensitive else filename.lower()
                
                # 匹配检查
                matched = False
                if exact_match:
                    # 精确匹配：文件名必须完全等于搜索模式
                    matched = (compare_name == search_pattern)
                else:
                    # 模糊匹配：文件名包含搜索模式
                    matched = (search_pattern in compare_name)
                
                if matched:
                    file_path = os.path.join(root, filename)
                    results.append(file_path)
        
        return results
    
    def display_results(self):
        """显示搜索结果"""
        self.results_list.clear()
        
        total_matches = 0
        
        # 显示文件名搜索结果
        if self.file_name_results:
            # 添加文件名搜索结果标题
            header_item = QListWidgetItem(f"📁 文件名匹配 ({len(self.file_name_results)} 个文件)")
            header_item.setData(Qt.UserRole, None)
            self.results_list.addItem(header_item)
            
            for file_path in self.file_name_results:
                import os
                file_item = QListWidgetItem(f"    📄 {file_path}")
                # 文件名匹配时，双击打开文件第一行
                file_item.setData(Qt.UserRole, (file_path, 1, 0))
                self.results_list.addItem(file_item)
                total_matches += 1
            
            # 添加分隔符
            if self.search_results:
                separator = QListWidgetItem("")
                separator.setData(Qt.UserRole, None)
                self.results_list.addItem(separator)
        
        # 显示文件内容搜索结果
        if self.search_results:
            # 添加文件内容搜索结果标题
            content_matches = sum(len(matches) for matches in self.search_results.values())
            header_item = QListWidgetItem(
                f"📝 文件内容匹配 ({len(self.search_results)} 个文件, {content_matches} 处匹配)"
            )
            header_item.setData(Qt.UserRole, None)
            self.results_list.addItem(header_item)
            
            # 按文件分组显示
            for file_path, matches in self.search_results.items():
                # 添加文件名作为分组标题
                file_item = QListWidgetItem(f"    📄 {file_path} ({len(matches)} 个匹配)")
                file_item.setData(Qt.UserRole, None)  # 标记为文件标题
                self.results_list.addItem(file_item)
                
                # 添加每个匹配项
                for match in matches:
                    match_text = f"        行 {match.line_number}: {match.line_content.strip()}"
                    match_item = QListWidgetItem(match_text)
                    match_item.setData(Qt.UserRole, (file_path, match.line_number, match.column))
                    self.results_list.addItem(match_item)
                    total_matches += 1
        
        # 更新结果计数
        file_count = len(self.file_name_results) + len(self.search_results)
        self.result_count_label.setText(
            f"结果: {file_count} 个文件, {total_matches} 处匹配"
        )
    
    def on_result_double_clicked(self, item: QListWidgetItem):
        """双击结果项"""
        data = item.data(Qt.UserRole)
        
        if data is not None:
            file_path, line_number, column = data
            self.result_clicked.emit(file_path, line_number, column)
    
    def showEvent(self, event):
        """对话框显示时"""
        super().showEvent(event)
        self.find_input.setFocus()
