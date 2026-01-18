"""
对话框单元测试
"""

import pytest
import tempfile
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.dialogs import FindDialog, FindInFilesDialog
from ui.editor_pane import EditorPane


@pytest.fixture
def app(qapp):
    """Qt应用程序fixture"""
    return qapp


class TestFindDialog:
    """查找对话框测试类"""
    
    def test_dialog_creation(self, app):
        """测试对话框创建"""
        dialog = FindDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "查找和替换"
    
    def test_set_editor(self, app):
        """测试设置编辑器"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world")
        
        dialog.set_editor(editor)
        assert dialog.current_editor == editor
    
    def test_find_simple_text(self, app):
        """测试简单文本查找"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world\nHello Python")
        dialog.set_editor(editor)
        
        # 输入查找文本
        dialog.find_input.setText("Hello")
        
        # 应该找到2个匹配
        assert len(dialog.matches) == 2
        # 标签应该显示 "匹配: 1/2" (当前位置/总数)
        assert "1/2" in dialog.match_count_label.text() or "匹配: 2" in dialog.match_count_label.text()
    
    def test_find_case_sensitive(self, app):
        """测试大小写敏感查找"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello hello HELLO")
        dialog.set_editor(editor)
        
        # 大小写不敏感
        dialog.case_sensitive_cb.setChecked(False)
        dialog.find_input.setText("Hello")
        assert len(dialog.matches) == 3
        
        # 大小写敏感
        dialog.case_sensitive_cb.setChecked(True)
        dialog.update_search()
        assert len(dialog.matches) == 1
    
    def test_find_regex(self, app):
        """测试正则表达式查找"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("test123\ntest456\nabc789")
        dialog.set_editor(editor)
        
        # 启用正则表达式
        dialog.regex_cb.setChecked(True)
        dialog.find_input.setText(r"test\d+")
        
        assert len(dialog.matches) == 2
    
    def test_find_next(self, app):
        """测试查找下一个"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world Hello Python")
        dialog.set_editor(editor)
        
        dialog.find_input.setText("Hello")
        
        # 初始应该在第一个匹配
        assert dialog.current_match_index == 0
        
        # 查找下一个
        dialog.on_find_next()
        assert dialog.current_match_index == 1
        
        # 再次查找应该循环回第一个
        dialog.on_find_next()
        assert dialog.current_match_index == 0
    
    def test_find_previous(self, app):
        """测试查找上一个"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world Hello Python")
        dialog.set_editor(editor)
        
        dialog.find_input.setText("Hello")
        
        # 初始在第一个，查找上一个应该到最后一个
        dialog.on_find_previous()
        assert dialog.current_match_index == 1
    
    def test_replace_current(self, app):
        """测试替换当前匹配"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world Hello Python")
        dialog.set_editor(editor)
        
        dialog.find_input.setText("Hello")
        dialog.replace_input.setText("Hi")
        
        # 替换第一个
        dialog.on_replace_current()
        
        text = editor.toPlainText()
        assert text.startswith("Hi world")
        assert "Hello Python" in text
    
    def test_replace_all(self, app, qtbot):
        """测试全部替换"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world Hello Python")
        dialog.set_editor(editor)
        
        dialog.find_input.setText("Hello")
        dialog.replace_input.setText("Hi")
        
        # 模拟点击全部替换按钮（会弹出消息框）
        with qtbot.waitSignal(dialog.replace_all_btn.clicked, timeout=1000):
            dialog.replace_all_btn.click()
        
        # 检查文本是否全部替换
        text = editor.toPlainText()
        assert "Hello" not in text
        assert text.count("Hi") == 2
    
    def test_empty_pattern(self, app):
        """测试空模式"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world")
        dialog.set_editor(editor)
        
        dialog.find_input.setText("")
        
        assert len(dialog.matches) == 0
        assert "匹配: 0" in dialog.match_count_label.text()
    
    def test_invalid_regex(self, app):
        """测试无效正则表达式"""
        dialog = FindDialog()
        editor = EditorPane()
        editor.setPlainText("Hello world")
        dialog.set_editor(editor)
        
        dialog.regex_cb.setChecked(True)
        dialog.find_input.setText("[invalid")
        
        assert "错误" in dialog.match_count_label.text()
        assert len(dialog.matches) == 0


class TestFindInFilesDialog:
    """跨文件搜索对话框测试类"""
    
    def test_dialog_creation(self, app):
        """测试对话框创建"""
        dialog = FindInFilesDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "在文件中查找"
    
    def test_browse_directory(self, app, qtbot):
        """测试浏览目录按钮"""
        dialog = FindInFilesDialog()
        
        # 检查按钮存在
        assert dialog.browse_btn is not None
    
    def test_search_in_files(self, app):
        """测试跨文件搜索"""
        dialog = FindInFilesDialog()
        
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test1.txt")
            file2 = os.path.join(tmpdir, "test2.txt")
            
            with open(file1, 'w', encoding='utf-8') as f:
                f.write("Hello world\nHello Python")
            
            with open(file2, 'w', encoding='utf-8') as f:
                f.write("Goodbye world")
            
            # 设置搜索参数
            dialog.find_input.setText("Hello")
            dialog.dir_input.setText(tmpdir)
            
            # 执行搜索
            dialog.on_search()
            
            # 检查结果
            assert len(dialog.search_results) == 1
            assert file1 in dialog.search_results
            assert len(dialog.search_results[file1]) == 2
    
    def test_search_with_file_filter(self, app):
        """测试带文件过滤的搜索"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test.txt")
            file2 = os.path.join(tmpdir, "test.py")
            
            with open(file1, 'w', encoding='utf-8') as f:
                f.write("Hello world")
            
            with open(file2, 'w', encoding='utf-8') as f:
                f.write("Hello Python")
            
            # 只搜索 .py 文件
            dialog.find_input.setText("Hello")
            dialog.dir_input.setText(tmpdir)
            dialog.filter_input.setText("*.py")
            
            dialog.on_search()
            
            # 应该只找到 .py 文件
            assert len(dialog.search_results) == 1
            assert file2 in dialog.search_results
    
    def test_display_results(self, app):
        """测试结果显示"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test.txt")
            
            with open(file1, 'w', encoding='utf-8') as f:
                f.write("Hello world\nHello Python")
            
            dialog.find_input.setText("Hello")
            dialog.dir_input.setText(tmpdir)
            dialog.on_search()
            
            # 检查结果列表
            assert dialog.results_list.count() > 0
            # 新格式：结果: 1 个文件, 2 处匹配
            assert "2 处匹配" in dialog.result_count_label.text()
    
    def test_empty_search_pattern(self, app, qtbot):
        """测试空搜索模式"""
        dialog = FindInFilesDialog()
        dialog.find_input.setText("")
        dialog.dir_input.setText("/some/path")
        
        # 应该显示警告
        dialog.on_search()
        
        # 结果应该为空
        assert len(dialog.search_results) == 0
    
    def test_empty_directory(self, app):
        """测试空目录"""
        dialog = FindInFilesDialog()
        dialog.find_input.setText("test")
        dialog.dir_input.setText("")
        
        dialog.on_search()
        
        assert len(dialog.search_results) == 0
    
    def test_result_clicked_signal(self, app, qtbot):
        """测试结果点击信号"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test.txt")
            
            with open(file1, 'w', encoding='utf-8') as f:
                f.write("Hello world")
            
            dialog.find_input.setText("Hello")
            dialog.dir_input.setText(tmpdir)
            dialog.on_search()
            
            # 新的结果格式有标题行，需要跳过更多项
            # 格式：标题 -> 文件名 -> 匹配行
            if dialog.results_list.count() > 2:
                match_item = dialog.results_list.item(2)  # 第3项是实际的匹配行
                
                # 测试信号
                with qtbot.waitSignal(dialog.result_clicked, timeout=1000):
                    dialog.on_result_double_clicked(match_item)
    
    def test_search_filename_fuzzy(self, app):
        """测试文件名模糊搜索"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            file1 = os.path.join(tmpdir, "test_file.txt")
            file2 = os.path.join(tmpdir, "another_test.py")
            file3 = os.path.join(tmpdir, "no_match.txt")
            
            for f in [file1, file2, file3]:
                with open(f, 'w', encoding='utf-8') as fp:
                    fp.write("content")
            
            # 设置搜索参数：只搜索文件名，模糊匹配
            dialog.find_input.setText("test")
            dialog.dir_input.setText(tmpdir)
            dialog.search_content_cb.setChecked(False)
            dialog.search_filename_cb.setChecked(True)
            dialog.fuzzy_match_cb.setChecked(True)
            dialog.exact_match_cb.setChecked(False)
            
            dialog.on_search()
            
            # 应该找到包含 "test" 的文件名
            assert len(dialog.file_name_results) == 2
            assert file1 in dialog.file_name_results
            assert file2 in dialog.file_name_results
            assert file3 not in dialog.file_name_results
    
    def test_search_filename_exact(self, app):
        """测试文件名精确搜索"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            file1 = os.path.join(tmpdir, "test.txt")
            file2 = os.path.join(tmpdir, "test_file.txt")
            
            for f in [file1, file2]:
                with open(f, 'w', encoding='utf-8') as fp:
                    fp.write("content")
            
            # 设置搜索参数：只搜索文件名，精确匹配
            dialog.find_input.setText("test.txt")
            dialog.dir_input.setText(tmpdir)
            dialog.search_content_cb.setChecked(False)
            dialog.search_filename_cb.setChecked(True)
            dialog.fuzzy_match_cb.setChecked(False)
            dialog.exact_match_cb.setChecked(True)
            
            dialog.on_search()
            
            # 应该只找到完全匹配的文件名
            assert len(dialog.file_name_results) == 1
            assert file1 in dialog.file_name_results
            assert file2 not in dialog.file_name_results
    
    def test_search_both_modes(self, app):
        """测试同时搜索文件名和内容"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            file1 = os.path.join(tmpdir, "hello.txt")
            file2 = os.path.join(tmpdir, "world.txt")
            
            with open(file1, 'w', encoding='utf-8') as f:
                f.write("some content")
            
            with open(file2, 'w', encoding='utf-8') as f:
                f.write("hello world")
            
            # 设置搜索参数：同时搜索文件名和内容
            dialog.find_input.setText("hello")
            dialog.dir_input.setText(tmpdir)
            dialog.search_content_cb.setChecked(True)
            dialog.search_filename_cb.setChecked(True)
            dialog.fuzzy_match_cb.setChecked(True)
            
            dialog.on_search()
            
            # 应该找到文件名匹配（file1）和内容匹配（file2）
            assert len(dialog.file_name_results) == 1  # hello.txt
            assert file1 in dialog.file_name_results
            assert len(dialog.search_results) == 1  # world.txt 包含 "hello"
            assert file2 in dialog.search_results
    
    def test_fuzzy_exact_mutual_exclusion(self, app):
        """测试模糊匹配和精确匹配互斥"""
        dialog = FindInFilesDialog()
        
        # 默认模糊匹配应该被选中
        assert dialog.fuzzy_match_cb.isChecked()
        assert not dialog.exact_match_cb.isChecked()
        
        # 选中精确匹配，模糊匹配应该取消
        dialog.exact_match_cb.setChecked(True)
        assert not dialog.fuzzy_match_cb.isChecked()
        assert dialog.exact_match_cb.isChecked()
        
        # 选中模糊匹配，精确匹配应该取消
        dialog.fuzzy_match_cb.setChecked(True)
        assert dialog.fuzzy_match_cb.isChecked()
        assert not dialog.exact_match_cb.isChecked()
    
    def test_no_search_mode_selected(self, app):
        """测试未选择搜索模式"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dialog.find_input.setText("test")
            dialog.dir_input.setText(tmpdir)
            
            # 取消所有搜索模式
            dialog.search_content_cb.setChecked(False)
            dialog.search_filename_cb.setChecked(False)
            
            dialog.on_search()
            
            # 应该没有结果
            assert len(dialog.search_results) == 0
            assert len(dialog.file_name_results) == 0
    
    def test_search_filename_case_sensitive(self, app):
        """测试文件名区分大小写搜索"""
        dialog = FindInFilesDialog()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件 - Windows 文件系统不区分大小写，所以只能创建一个
            # 我们改用不同的文件名来测试
            file1 = os.path.join(tmpdir, "Test_File.txt")
            file2 = os.path.join(tmpdir, "test_data.txt")
            
            for f in [file1, file2]:
                with open(f, 'w', encoding='utf-8') as fp:
                    fp.write("content")
            
            # 不区分大小写 - 搜索 "test"
            dialog.find_input.setText("test")
            dialog.dir_input.setText(tmpdir)
            dialog.search_content_cb.setChecked(False)
            dialog.search_filename_cb.setChecked(True)
            dialog.case_sensitive_cb.setChecked(False)
            
            dialog.on_search()
            assert len(dialog.file_name_results) == 2  # 两个文件都包含 "test"（不区分大小写）
            
            # 区分大小写 - 搜索 "test"
            dialog.case_sensitive_cb.setChecked(True)
            dialog.on_search()
            assert len(dialog.file_name_results) == 1  # 只有 test_data.txt 匹配
            assert file2 in dialog.file_name_results


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
