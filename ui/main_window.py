"""
主窗口模块

应用程序的主入口，管理整体布局和顶层交互。
"""

from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QApplication, QPlainTextEdit, QComboBox, QLabel
)
from PySide6.QtCore import Qt, QUrl, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent, QTextCursor
from ui.tab_widget import TabWidget
from ui.editor_pane import EditorPane
from ui.dialogs import FindDialog, FindInFilesDialog
from core.file_manager import FileManager
from core.history_manager import HistoryManager
from themes.theme_manager import ThemeManager
from utils.language_detector import LanguageDetector
import os
import json
import tempfile
from datetime import datetime


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化管理器
        self.file_manager = FileManager()
        self.history_manager = HistoryManager()
        self.theme_manager = ThemeManager()
        self.language_detector = LanguageDetector()
        
        # 当前缩放级别
        self.current_zoom_level = 0
        
        # 对话框
        self.find_dialog = None
        self.find_in_files_dialog = None
        
        # 自动保存目录
        self.autosave_dir = os.path.join(tempfile.gettempdir(), 'publime_autosave')
        os.makedirs(self.autosave_dir, exist_ok=True)
        
        # 设置窗口
        self.setWindowTitle("Publime - 文本编辑器")
        self.resize(1200, 800)
        
        # 启用拖放
        self.setAcceptDrops(True)
        
        # 创建UI组件
        self.setup_ui()
        
        # 加载历史记录
        self.history_manager.load_from_disk()
        
        # 应用默认主题（深色）
        self.theme_manager.set_current_theme("Dark")
        self.apply_theme("Dark")
        
        # 检查崩溃恢复
        self.check_crash_recovery()
        
        # 如果没有恢复任何文件，创建一个新文件
        if self.tab_widget.count() == 0:
            self.new_file()
        
        # 设置自动保存定时器（每5分钟）
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.auto_save_all)
        self.autosave_timer.start(5 * 60 * 1000)  # 5分钟 = 300000毫秒
    
    def setup_ui(self):
        """设置UI"""
        # 创建标签页容器
        self.tab_widget = TabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # 连接标签页关闭信号
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # 连接标签页切换信号，用于更新状态栏
        self.tab_widget.currentChanged.connect(self.update_statusbar)
        
        # 连接双击空白区域信号
        self.tab_widget.double_click_empty.connect(self.new_file)
        
        # 创建菜单栏
        self.create_menus()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.create_statusbar()
    
    def create_statusbar(self):
        """创建状态栏，包含编码和语言选择器"""
        statusbar = self.statusBar()
        
        # 状态消息标签（左侧）
        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label)
        
        # 添加弹簧，将右侧控件推到右边
        statusbar.addPermanentWidget(QLabel(""))
        
        # 语言选择器
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "Plain Text",
            "Python",
            "Java",
            "JavaScript",
            "SQL",
            "JSON",
            "Kotlin",
            "Markdown",
            "XML",
            "YAML"
        ])
        self.language_combo.setMinimumWidth(120)
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        statusbar.addPermanentWidget(QLabel("语言: "))
        statusbar.addPermanentWidget(self.language_combo)
        
        # 编码选择器
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems([
            "UTF-8",
            "GBK",
            "GB2312",
            "UTF-16",
            "ASCII",
            "ISO-8859-1"
        ])
        self.encoding_combo.setMinimumWidth(100)
        self.encoding_combo.currentTextChanged.connect(self.on_encoding_changed)
        statusbar.addPermanentWidget(QLabel("编码: "))
        statusbar.addPermanentWidget(self.encoding_combo)
    
    def create_menus(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为(&A)...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 最近文件菜单
        self.recent_menu = file_menu.addMenu("最近文件(&R)")
        self.update_recent_files_menu()
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        undo_action = QAction("撤销(&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做(&R)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("剪切(&T)", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("复制(&C)", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴(&P)", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        # 自动换行选项
        self.word_wrap_action = QAction("自动换行(&W)", self)
        self.word_wrap_action.setCheckable(True)
        self.word_wrap_action.setChecked(False)  # 默认不换行
        self.word_wrap_action.triggered.connect(self.toggle_word_wrap)
        edit_menu.addAction(self.word_wrap_action)
        
        edit_menu.addSeparator()
        
        # 格式化菜单 - 自动检测语言
        format_action = QAction("格式化(&F)", self)
        format_action.setShortcut(QKeySequence("Ctrl+Alt+F"))
        format_action.triggered.connect(self.format_code)
        edit_menu.addAction(format_action)
        
        # 搜索菜单
        search_menu = menubar.addMenu("搜索(&S)")
        
        find_action = QAction("查找(&F)...", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_find_dialog)
        search_menu.addAction(find_action)
        
        find_in_files_action = QAction("在文件夹中查找(&I)...", self)
        find_in_files_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        find_in_files_action.triggered.connect(self.show_find_in_files_dialog)
        search_menu.addAction(find_in_files_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        toggle_theme_action = QAction("切换主题(&T)", self)
        toggle_theme_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        toggle_theme_action.triggered.connect(self.toggle_theme)
        help_menu.addAction(toggle_theme_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        # 工具栏已移除，保留方法以避免破坏现有代码
        pass
    
    def update_recent_files_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()
        
        recent_files = self.history_manager.get_recent_files()
        
        if not recent_files:
            no_recent_action = QAction("(无最近文件)", self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
            return
        
        for file_path in recent_files[:10]:  # 只显示前10个
            action = QAction(file_path, self)
            action.triggered.connect(lambda checked, path=file_path: self.open_file(path))
            self.recent_menu.addAction(action)
        
        self.recent_menu.addSeparator()
        
        clear_action = QAction("清空历史记录", self)
        clear_action.triggered.connect(self.clear_history)
        self.recent_menu.addAction(clear_action)
    
    def new_file(self):
        """新建文件"""
        editor = EditorPane()
        index = self.tab_widget.addTab(editor, "未命名")
        self.tab_widget.setCurrentIndex(index)
        self.apply_current_theme_to_editor(editor)
    
    def open_file(self, file_path=None):
        """
        打开文件
        
        Args:
            file_path: 文件路径，如果为None或False则显示文件选择对话框
        """
        # 处理Qt信号传递的checked参数（布尔值）
        if file_path is None or file_path is False or file_path == "":
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "打开文件",
                "",
                "所有文件 (*);;文本文件 (*.txt);;Python文件 (*.py);;Java文件 (*.java)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
        
        if not file_path or file_path is False:
            return
        
        # 检查文件是否已打开
        existing_index = self.tab_widget.find_tab_by_file_path(file_path)
        if existing_index >= 0:
            self.tab_widget.setCurrentIndex(existing_index)
            return
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            QMessageBox.critical(
                self,
                "文件不存在",
                f"文件不存在: {file_path}"
            )
            return
        
        # 检查是否为大文件
        try:
            if self.file_manager.is_large_file(file_path, threshold_mb=50):
                reply = QMessageBox.warning(
                    self,
                    "大文件警告",
                    f"文件大小超过 50MB，打开可能需要较长时间。\n是否继续？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        except Exception:
            pass  # 如果无法检测文件大小，继续尝试打开
        
        # 读取文件
        try:
            content = self.file_manager.read_file(file_path)
            
            # 创建编辑器
            editor = EditorPane()
            editor.setPlainText(content)
            editor.set_file_path(file_path)
            
            # 检测语言并设置语法高亮
            # 对于超大文件（>10MB），禁用语法高亮以提高性能
            try:
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb <= 10:
                    language = self.language_detector.detect_language(file_path)
                    editor.set_language(language)
                else:
                    # 大文件禁用语法高亮
                    self.statusBar().showMessage("大文件已禁用语法高亮以提高性能", 5000)
            except Exception:
                pass  # 如果语法高亮失败，继续
            
            # 添加到标签页
            file_name = os.path.basename(file_path)
            index = self.tab_widget.addTab(editor, file_name)
            self.tab_widget.setCurrentIndex(index)
            
            # 应用主题
            self.apply_current_theme_to_editor(editor)
            
            # 更新状态栏（显示正确的语言）
            self.update_statusbar()
            
            # 添加到历史记录
            self.history_manager.add_file(file_path)
            self.update_recent_files_menu()
            
            self.statusBar().showMessage(f"已打开: {file_path}", 3000)
        
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "文件不存在",
                f"文件不存在: {file_path}"
            )
        except PermissionError:
            QMessageBox.critical(
                self,
                "权限不足",
                f"没有读取权限: {file_path}"
            )
        except UnicodeDecodeError:
            QMessageBox.critical(
                self,
                "编码错误",
                f"无法识别文件编码，可能是二进制文件或使用了不支持的编码格式。\n文件: {file_path}"
            )
        except MemoryError:
            QMessageBox.critical(
                self,
                "内存不足",
                f"文件过大，内存不足以打开。\n文件: {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"无法打开文件: {str(e)}"
            )
    
    def save_file(self) -> bool:
        """
        保存当前文件
        
        Returns:
            是否保存成功
        """
        editor = self.tab_widget.get_current_editor()
        if not editor:
            return False
        
        file_path = editor.get_file_path()
        
        # 如果没有文件路径，使用另存为
        if not file_path:
            return self.save_file_as()
        
        # 保存文件
        try:
            content = editor.toPlainText()
            self.file_manager.write_file(file_path, content)
            
            # 清除修改标记
            editor.document().setModified(False)
            self.tab_widget.update_tab_title(self.tab_widget.currentIndex())
            
            self.statusBar().showMessage(f"已保存: {file_path}", 3000)
            return True
        
        except PermissionError:
            QMessageBox.critical(
                self,
                "权限不足",
                f"没有写入权限: {file_path}"
            )
            return False
        except OSError as e:
            # 处理磁盘空间不足等错误
            error_msg = str(e)
            if "No space left" in error_msg or "磁盘空间不足" in error_msg:
                QMessageBox.critical(
                    self,
                    "磁盘空间不足",
                    f"磁盘空间不足，无法保存文件。\n文件: {file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "IO错误",
                    f"保存文件时发生错误: {error_msg}\n文件: {file_path}"
                )
            return False
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"无法保存文件: {str(e)}"
            )
            return False
    
    def save_file_as(self) -> bool:
        """
        另存为
        
        Returns:
            是否保存成功
        """
        editor = self.tab_widget.get_current_editor()
        if not editor:
            return False
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "另存为",
            "",
            "所有文件 (*);;文本文件 (*.txt);;Python文件 (*.py);;Java文件 (*.java)"
            # 使用系统原生对话框
        )
        
        if not file_path:
            return False
        
        # 保存文件
        try:
            content = editor.toPlainText()
            self.file_manager.write_file(file_path, content)
            
            # 更新编辑器文件路径
            editor.set_file_path(file_path)
            
            # 检测语言并更新语法高亮
            language = self.language_detector.detect_language(file_path)
            editor.set_language(language)
            
            # 更新标签页标题
            file_name = os.path.basename(file_path)
            self.tab_widget.setTabText(self.tab_widget.currentIndex(), file_name)
            
            # 清除修改标记
            editor.document().setModified(False)
            self.tab_widget.update_tab_title(self.tab_widget.currentIndex())
            
            # 添加到历史记录
            self.history_manager.add_file(file_path)
            self.update_recent_files_menu()
            
            self.statusBar().showMessage(f"已保存: {file_path}", 3000)
            return True
        
        except PermissionError:
            QMessageBox.critical(
                self,
                "权限不足",
                f"没有写入权限: {file_path}"
            )
            return False
        except OSError as e:
            # 处理磁盘空间不足等错误
            error_msg = str(e)
            if "No space left" in error_msg or "磁盘空间不足" in error_msg:
                QMessageBox.critical(
                    self,
                    "磁盘空间不足",
                    f"磁盘空间不足，无法保存文件。\n文件: {file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "IO错误",
                    f"保存文件时发生错误: {error_msg}\n文件: {file_path}"
                )
            return False
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"无法保存文件: {str(e)}"
            )
            return False
    
    def close_tab(self, index: int) -> None:
        """
        关闭标签页
        
        Args:
            index: 标签页索引
        """
        editor = self.tab_widget.get_editor_at(index)
        if not editor:
            return
        
        # 检查是否有未保存的修改
        if editor.document().isModified():
            file_path = editor.get_file_path()
            file_name = os.path.basename(file_path) if file_path else "未命名"
            
            # 创建自定义消息框以使用中文按钮
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("保存更改")
            msg_box.setText(f"文件 '{file_name}' 已修改，是否保存？")
            msg_box.setIcon(QMessageBox.Question)
            
            # 添加中文按钮
            save_button = msg_box.addButton("保存", QMessageBox.AcceptRole)
            discard_button = msg_box.addButton("不保存", QMessageBox.DestructiveRole)
            cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
            
            msg_box.setDefaultButton(save_button)
            msg_box.exec()
            
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == save_button:
                # 切换到该标签页以便保存
                self.tab_widget.setCurrentIndex(index)
                if not self.save_file():
                    return
            elif clicked_button == cancel_button:
                return
            # 如果点击"不保存"，继续关闭
        
        self.tab_widget.close_tab(index)
    
    def undo(self):
        """撤销"""
        editor = self.tab_widget.get_current_editor()
        if editor:
            editor.undo()
    
    def redo(self):
        """重做"""
        editor = self.tab_widget.get_current_editor()
        if editor:
            editor.redo()
    
    def cut(self):
        """剪切"""
        editor = self.tab_widget.get_current_editor()
        if editor:
            editor.cut()
    
    def copy(self):
        """复制"""
        editor = self.tab_widget.get_current_editor()
        if editor:
            editor.copy()
    
    def paste(self):
        """粘贴"""
        editor = self.tab_widget.get_current_editor()
        if editor:
            editor.paste()
    
    def toggle_word_wrap(self):
        """切换自动换行"""
        enabled = self.word_wrap_action.isChecked()
        
        # 应用到所有编辑器
        for editor in self.tab_widget.get_all_editors():
            if enabled:
                editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            else:
                editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        self.statusBar().showMessage(f"自动换行: {'开启' if enabled else '关闭'}", 2000)
    
    def format_code(self):
        """自动检测语言并格式化代码"""
        editor = self.tab_widget.get_current_editor()
        if not editor:
            return
        
        # 获取当前文件的语言
        file_path = editor.get_file_path()
        language = None
        
        if file_path:
            # 通过文件扩展名检测语言
            language = self.language_detector.detect_language(file_path)
        else:
            # 如果没有文件路径，尝试通过内容检测
            text = editor.toPlainText().strip()
            if text:
                # 尝试解析为 JSON
                try:
                    import json
                    json.loads(text)
                    language = "json"
                except:
                    # 检查是否包含 SQL 关键字
                    sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'TABLE']
                    text_upper = text.upper()
                    if any(keyword in text_upper for keyword in sql_keywords):
                        language = "sql"
        
        # 根据语言执行格式化
        if language and language.lower() == "json":
            self.format_json()
        elif language and language.lower() == "sql":
            self.format_sql()
        else:
            self.statusBar().showMessage("当前文件不是 JSON 或 SQL 格式，无需格式化", 3000)
    
    def format_json(self):
        """格式化 JSON"""
        editor = self.tab_widget.get_current_editor()
        if not editor:
            return
        
        try:
            import json
            
            # 获取当前文本
            text = editor.toPlainText()
            
            # 解析并格式化 JSON
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            
            # 设置格式化后的文本
            editor.setPlainText(formatted)
            
            self.statusBar().showMessage("JSON 格式化成功", 2000)
        
        except json.JSONDecodeError as e:
            QMessageBox.warning(
                self,
                "JSON 格式化失败",
                f"无效的 JSON 格式:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"格式化失败: {str(e)}"
            )
    
    def format_sql(self):
        """格式化 SQL"""
        editor = self.tab_widget.get_current_editor()
        if not editor:
            return
        
        try:
            # 使用新的 SQL 格式化器
            from sql_formatter_new import format_sql as format_sql_text
            
            # 获取当前文本
            text = editor.toPlainText()
            
            # 格式化
            formatted_text = format_sql_text(text)
            
            # 设置格式化后的文本
            editor.setPlainText(formatted_text)
            
            self.statusBar().showMessage("SQL 格式化成功", 2000)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"格式化失败: {str(e)}"
            )
    
    def show_find_dialog(self):
        """显示查找对话框"""
        if not self.find_dialog:
            self.find_dialog = FindDialog(self)
        
        editor = self.tab_widget.get_current_editor()
        if editor:
            self.find_dialog.set_editor(editor)
            self.find_dialog.show()
            self.find_dialog.raise_()
            self.find_dialog.activateWindow()
    
    def show_find_in_files_dialog(self):
        """显示跨文件搜索对话框"""
        if not self.find_in_files_dialog:
            self.find_in_files_dialog = FindInFilesDialog(self)
            self.find_in_files_dialog.result_clicked.connect(self.on_search_result_clicked)
        
        self.find_in_files_dialog.show()
        self.find_in_files_dialog.raise_()
        self.find_in_files_dialog.activateWindow()
    
    def on_search_result_clicked(self, file_path: str, line_number: int, column: int):
        """
        处理搜索结果点击
        
        Args:
            file_path: 文件路径
            line_number: 行号
            column: 列号
        """
        # 打开文件
        self.open_file(file_path)
        
        # 跳转到指定位置
        editor = self.tab_widget.get_current_editor()
        if editor:
            # 移动到指定行
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(line_number - 1):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, column)
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()
    
    def zoom_in(self):
        """放大字体"""
        self.current_zoom_level += 1
        self.apply_zoom()
    
    def zoom_out(self):
        """缩小字体"""
        self.current_zoom_level -= 1
        self.apply_zoom()
    
    def reset_zoom(self):
        """重置缩放"""
        self.current_zoom_level = 0
        self.apply_zoom()
    
    def apply_zoom(self):
        """应用缩放到所有编辑器"""
        for editor in self.tab_widget.get_all_editors():
            editor.apply_zoom(self.current_zoom_level)
    
    def toggle_theme(self):
        """切换主题"""
        current_theme = self.theme_manager.get_current_theme()
        # 根据当前主题名称切换
        new_theme_name = "Light" if current_theme.name == "Dark" else "Dark"
        self.theme_manager.set_current_theme(new_theme_name)
        self.apply_theme(new_theme_name)
    
    def apply_theme(self, theme_name: str):
        """
        应用主题
        
        Args:
            theme_name: 主题名称
        """
        theme = self.theme_manager.get_theme(theme_name)
        if theme:
            self.theme_manager.set_current_theme(theme_name)
            
            # 根据主题计算不同区域的背景色
            if theme_name == "Dark":
                # 深色主题
                menubar_bg = "#1e1e1e"  # 菜单栏：更深的灰色
                tab_bar_bg = "#2d2d2d"  # 标签栏：中等灰色
                editor_bg = theme.background  # 编辑器：#252526（原背景色）
                tab_selected_bg = "#37373d"  # 选中标签：稍亮的灰色
                border_color = "#3e3e42"  # 边框颜色
            else:
                # 浅色主题
                menubar_bg = "#f3f3f3"  # 菜单栏：浅灰色
                tab_bar_bg = "#e8e8e8"  # 标签栏：稍深的灰色
                editor_bg = theme.background  # 编辑器：#ffffff（原背景色）
                tab_selected_bg = "#ffffff"  # 选中标签：白色
                border_color = "#d4d4d4"  # 边框颜色
            
            # 应用主题到主窗口
            window_style = f"""
                QMainWindow {{
                    background-color: {editor_bg};
                    color: {theme.foreground};
                }}
                QMenuBar {{
                    background-color: {menubar_bg};
                    color: {theme.foreground};
                    padding: 4px;
                    border-bottom: 1px solid {border_color};
                }}
                QMenuBar::item {{
                    padding: 4px 8px;
                    background-color: transparent;
                }}
                QMenuBar::item:selected {{
                    background-color: {theme.selection_bg};
                }}
                QMenu {{
                    background-color: {menubar_bg};
                    color: {theme.foreground};
                    border: 1px solid {border_color};
                }}
                QMenu::item {{
                    padding: 5px 25px;
                }}
                QMenu::item:selected {{
                    background-color: {theme.selection_bg};
                }}
                QStatusBar {{
                    background-color: {menubar_bg};
                    color: {theme.foreground};
                    border-top: 1px solid {border_color};
                }}
                QStatusBar QLabel {{
                    color: {theme.foreground};
                    background-color: transparent;
                }}
                QComboBox {{
                    background-color: {tab_bar_bg};
                    color: {theme.foreground};
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    padding: 3px 8px;
                    min-height: 20px;
                }}
                QComboBox:hover {{
                    border: 1px solid {theme.selection_bg};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid {theme.foreground};
                    margin-right: 5px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {tab_bar_bg};
                    color: {theme.foreground};
                    selection-background-color: {theme.selection_bg};
                    selection-color: {theme.selection_fg};
                    border: 1px solid {border_color};
                }}
                QTabWidget::pane {{
                    background-color: {editor_bg};
                    border: none;
                    border-top: 1px solid {border_color};
                }}
                QTabBar {{
                    background-color: {tab_bar_bg};
                }}
                QTabBar::tab {{
                    background-color: {tab_bar_bg};
                    color: {theme.foreground};
                    padding: 8px 16px;
                    border: none;
                    border-right: 1px solid {border_color};
                    margin: 0px;
                }}
                QTabBar::tab:selected {{
                    background-color: {tab_selected_bg};
                    border-bottom: 2px solid {theme.selection_bg};
                }}
                QTabBar::tab:hover {{
                    background-color: {tab_selected_bg};
                }}
            """
            self.setStyleSheet(window_style)
            
            # 应用到所有编辑器
            for editor in self.tab_widget.get_all_editors():
                editor.apply_theme(theme)
    
    def apply_current_theme_to_editor(self, editor: EditorPane):
        """
        应用当前主题到编辑器
        
        Args:
            editor: 编辑器窗格
        """
        theme = self.theme_manager.get_current_theme()
        editor.apply_theme(theme)
    
    def clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self,
            "清空历史记录",
            "确定要清空所有历史记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.history_manager.save_to_disk()
            self.update_recent_files_menu()
    
    def on_language_changed(self, language_name: str):
        """语言选择器改变时的处理"""
        editor = self.tab_widget.get_current_editor()
        if not editor:
            return
        
        # 映射显示名称到内部语言名称
        language_map = {
            "Plain Text": None,
            "Python": "python",
            "Java": "java",
            "JavaScript": "javascript",
            "SQL": "sql",
            "JSON": "json",
            "Kotlin": "kotlin",
            "Markdown": "markdown",
            "XML": None,
            "YAML": None
        }
        
        language = language_map.get(language_name)
        if language:
            editor.set_language(language)
            self.status_label.setText(f"语言已切换为: {language_name}")
        else:
            # 对于不支持语法高亮的语言，清除高亮
            editor.set_language(None)
            self.status_label.setText(f"语言已切换为: {language_name}")
    
    def on_encoding_changed(self, encoding: str):
        """编码选择器改变时的处理"""
        editor = self.tab_widget.get_current_editor()
        if not editor:
            return
        
        file_path = editor.get_file_path()
        if not file_path:
            self.status_label.setText(f"编码已设置为: {encoding}")
            return
        
        # 重新读取文件，使用新的编码
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # 保存当前光标位置
            cursor = editor.textCursor()
            position = cursor.position()
            
            # 设置新内容
            editor.setPlainText(content)
            
            # 恢复光标位置
            cursor.setPosition(min(position, len(content)))
            editor.setTextCursor(cursor)
            
            self.status_label.setText(f"文件已用 {encoding} 编码重新加载")
        except UnicodeDecodeError:
            QMessageBox.warning(
                self,
                "编码错误",
                f"无法使用 {encoding} 编码读取文件"
            )
            # 恢复到UTF-8
            self.encoding_combo.setCurrentText("UTF-8")
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"重新加载文件失败: {str(e)}"
            )
    
    def update_statusbar(self):
        """更新状态栏信息"""
        editor = self.tab_widget.get_current_editor()
        if not editor:
            self.language_combo.setCurrentText("Plain Text")
            self.encoding_combo.setCurrentText("UTF-8")
            return
        
        # 更新语言显示
        file_path = editor.get_file_path()
        if file_path:
            language = self.language_detector.detect_language(file_path)
            language_display_map = {
                "python": "Python",
                "java": "Java",
                "javascript": "JavaScript",
                "sql": "SQL",
                "json": "JSON",
                "kotlin": "Kotlin",
                "markdown": "Markdown",
                "xml": "XML",
                "yaml": "YAML",
                None: "Plain Text"
            }
            display_name = language_display_map.get(language, "Plain Text")
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentText(display_name)
            self.language_combo.blockSignals(False)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 Publime",
            "Publime 文本编辑器\n\n"
            "一个使用 Python 和 PySide6 实现的文本编辑器\n"
            "作为 Sublime Text 的平替方案"
        )
    
    def auto_save_all(self):
        """自动保存所有打开的文件"""
        try:
            autosave_data = {
                'timestamp': datetime.now().isoformat(),
                'files': []
            }
            
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.get_editor_at(i)
                if not editor:
                    continue
                
                file_path = editor.get_file_path()
                content = editor.toPlainText()
                is_modified = editor.document().isModified()
                
                # 为每个文件创建自动保存副本
                if file_path:
                    # 使用文件路径的哈希作为自动保存文件名
                    import hashlib
                    file_hash = hashlib.md5(file_path.encode()).hexdigest()
                    autosave_file = os.path.join(self.autosave_dir, f"{file_hash}.txt")
                else:
                    # 未命名文件使用索引
                    autosave_file = os.path.join(self.autosave_dir, f"untitled_{i}.txt")
                
                # 保存内容
                try:
                    with open(autosave_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    autosave_data['files'].append({
                        'original_path': file_path,
                        'autosave_path': autosave_file,
                        'is_modified': is_modified,
                        'tab_index': i
                    })
                except Exception:
                    pass  # 忽略单个文件的保存错误
            
            # 保存元数据
            metadata_file = os.path.join(self.autosave_dir, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(autosave_data, f, indent=2)
        
        except Exception:
            pass  # 自动保存失败不应该影响用户操作
    
    def check_crash_recovery(self):
        """检查是否有崩溃恢复数据"""
        metadata_file = os.path.join(self.autosave_dir, 'metadata.json')
        
        if not os.path.exists(metadata_file):
            return
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                autosave_data = json.load(f)
            
            # 检查是否有文件需要恢复
            if not autosave_data.get('files'):
                return
            
            # 询问用户是否恢复
            reply = QMessageBox.question(
                self,
                "崩溃恢复",
                f"检测到上次未正常关闭的会话（{autosave_data.get('timestamp', '未知时间')}）。\n"
                f"是否恢复 {len(autosave_data['files'])} 个文件？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 恢复文件
                for file_info in autosave_data['files']:
                    autosave_path = file_info.get('autosave_path')
                    original_path = file_info.get('original_path')
                    
                    if not os.path.exists(autosave_path):
                        continue
                    
                    try:
                        # 读取自动保存的内容
                        with open(autosave_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 创建编辑器
                        editor = EditorPane()
                        editor.setPlainText(content)
                        
                        if original_path:
                            editor.set_file_path(original_path)
                            language = self.language_detector.detect_language(original_path)
                            editor.set_language(language)
                            file_name = os.path.basename(original_path)
                        else:
                            file_name = "未命名"
                        
                        # 添加到标签页
                        index = self.tab_widget.addTab(editor, file_name)
                        
                        # 如果文件被修改过，标记为已修改
                        if file_info.get('is_modified'):
                            editor.document().setModified(True)
                            self.tab_widget.update_tab_title(index)
                        
                        # 应用主题
                        self.apply_current_theme_to_editor(editor)
                    
                    except Exception:
                        pass  # 忽略单个文件的恢复错误
                
                self.statusBar().showMessage("已恢复上次会话", 3000)
            
            # 清理自动保存文件
            self.clear_autosave_files()
        
        except Exception:
            pass  # 恢复失败不应该阻止程序启动
    
    def clear_autosave_files(self):
        """清理自动保存文件"""
        try:
            for file in os.listdir(self.autosave_dir):
                file_path = os.path.join(self.autosave_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception:
            pass
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """拖放事件"""
        urls = event.mimeData().urls()
        
        for url in urls:
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.open_file(file_path)
        
        event.acceptProposedAction()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 检查所有标签页是否有未保存的修改
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.get_editor_at(i)
            if editor and editor.document().isModified():
                file_path = editor.get_file_path()
                file_name = os.path.basename(file_path) if file_path else "未命名"
                
                # 创建自定义消息框以使用中文按钮
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("保存更改")
                msg_box.setText(f"文件 '{file_name}' 已修改，是否保存？")
                msg_box.setIcon(QMessageBox.Question)
                
                # 添加中文按钮
                save_button = msg_box.addButton("保存", QMessageBox.AcceptRole)
                discard_button = msg_box.addButton("不保存", QMessageBox.DestructiveRole)
                cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
                
                msg_box.setDefaultButton(save_button)
                msg_box.exec()
                
                clicked_button = msg_box.clickedButton()
                
                if clicked_button == save_button:
                    self.tab_widget.setCurrentIndex(i)
                    if not self.save_file():
                        event.ignore()
                        return
                elif clicked_button == cancel_button:
                    event.ignore()
                    return
                # 如果点击"不保存"，继续关闭
        
        # 正常关闭时清理自动保存文件
        self.clear_autosave_files()
        
        # 保存历史记录
        self.history_manager.save_to_disk()
        
        event.accept()
