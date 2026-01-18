"""
搜索引擎单元测试
"""

import pytest
import tempfile
import os
from core.search_engine import SearchEngine, Match


class TestSearchEngine:
    """搜索引擎测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.engine = SearchEngine()
    
    def test_find_simple_text(self):
        """测试简单文本搜索"""
        text = "Hello world\nHello Python\nGoodbye world"
        matches = self.engine.find_in_text(text, "Hello")
        
        assert len(matches) == 2
        assert matches[0].line_number == 1
        assert matches[0].column == 0
        assert matches[0].matched_text == "Hello"
        assert matches[1].line_number == 2
        assert matches[1].column == 0
    
    def test_find_case_sensitive(self):
        """测试大小写敏感搜索"""
        text = "Hello hello HELLO"
        
        # 大小写敏感
        matches = self.engine.find_in_text(text, "Hello", case_sensitive=True)
        assert len(matches) == 1
        assert matches[0].matched_text == "Hello"
        
        # 大小写不敏感
        matches = self.engine.find_in_text(text, "Hello", case_sensitive=False)
        assert len(matches) == 3
    
    def test_find_regex(self):
        """测试正则表达式搜索"""
        text = "test123\ntest456\nabc789"
        
        # 查找 test 后跟数字
        matches = self.engine.find_in_text(text, r"test\d+", regex=True)
        assert len(matches) == 2
        assert matches[0].matched_text == "test123"
        assert matches[1].matched_text == "test456"
    
    def test_find_empty_pattern(self):
        """测试空模式"""
        text = "Hello world"
        matches = self.engine.find_in_text(text, "")
        assert len(matches) == 0
    
    def test_find_no_matches(self):
        """测试无匹配"""
        text = "Hello world"
        matches = self.engine.find_in_text(text, "Python")
        assert len(matches) == 0
    
    def test_find_overlapping(self):
        """测试重叠匹配"""
        text = "aaa"
        matches = self.engine.find_in_text(text, "aa")
        # 应该找到两个重叠的匹配: 位置0和位置1
        assert len(matches) == 2
    
    def test_replace_single(self):
        """测试单项替换"""
        text = "Hello world Hello Python"
        new_text, count = self.engine.replace_in_text(
            text, "Hello", "Hi", replace_all=False
        )
        
        assert count == 1
        assert new_text == "Hi world Hello Python"
    
    def test_replace_all(self):
        """测试全部替换"""
        text = "Hello world Hello Python"
        new_text, count = self.engine.replace_in_text(
            text, "Hello", "Hi", replace_all=True
        )
        
        assert count == 2
        assert new_text == "Hi world Hi Python"
    
    def test_replace_case_insensitive(self):
        """测试大小写不敏感替换"""
        text = "Hello hello HELLO"
        new_text, count = self.engine.replace_in_text(
            text, "hello", "Hi", case_sensitive=False, replace_all=True
        )
        
        assert count == 3
        assert new_text == "Hi Hi Hi"
    
    def test_replace_regex(self):
        """测试正则表达式替换"""
        text = "test123 test456"
        new_text, count = self.engine.replace_in_text(
            text, r"test(\d+)", r"result\1", regex=True, replace_all=True
        )
        
        assert count == 2
        assert new_text == "result123 result456"
    
    def test_replace_no_match(self):
        """测试无匹配的替换"""
        text = "Hello world"
        new_text, count = self.engine.replace_in_text(
            text, "Python", "Java"
        )
        
        assert count == 0
        assert new_text == text
    
    def test_invalid_regex(self):
        """测试无效的正则表达式"""
        text = "Hello world"
        
        with pytest.raises(ValueError, match="Invalid regular expression"):
            self.engine.find_in_text(text, "[invalid", regex=True)
        
        with pytest.raises(ValueError, match="Invalid regular expression"):
            self.engine.replace_in_text(text, "[invalid", "test", regex=True)
    
    def test_match_positions(self):
        """测试匹配位置信息"""
        text = "Hello\nworld"
        matches = self.engine.find_in_text(text, "world")
        
        assert len(matches) == 1
        match = matches[0]
        assert match.line_number == 2
        assert match.column == 0
        assert match.start_pos == 6  # "Hello\n" = 6 characters
        assert match.end_pos == 11  # 6 + len("world")
        assert match.line_content == "world"
    
    def test_find_in_files(self):
        """测试跨文件搜索"""
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            file1 = os.path.join(tmpdir, "test1.txt")
            file2 = os.path.join(tmpdir, "test2.txt")
            file3 = os.path.join(tmpdir, "test3.py")
            
            with open(file1, 'w', encoding='utf-8') as f:
                f.write("Hello world\nHello Python")
            
            with open(file2, 'w', encoding='utf-8') as f:
                f.write("Goodbye world")
            
            with open(file3, 'w', encoding='utf-8') as f:
                f.write("print('Hello')")
            
            # 搜索所有文件
            results = self.engine.find_in_files(tmpdir, "Hello")
            
            assert len(results) == 2  # file1 和 file3
            assert file1 in results
            assert file3 in results
            assert len(results[file1]) == 2  # file1 中有两个 Hello
            assert len(results[file3]) == 1  # file3 中有一个 Hello
    
    def test_find_in_files_with_filter(self):
        """测试带文件类型过滤的跨文件搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            file1 = os.path.join(tmpdir, "test.txt")
            file2 = os.path.join(tmpdir, "test.py")
            
            with open(file1, 'w', encoding='utf-8') as f:
                f.write("Hello world")
            
            with open(file2, 'w', encoding='utf-8') as f:
                f.write("Hello Python")
            
            # 只搜索 .py 文件
            results = self.engine.find_in_files(
                tmpdir, "Hello", file_patterns=["*.py"]
            )
            
            assert len(results) == 1
            assert file2 in results
            assert file1 not in results
    
    def test_find_in_files_invalid_directory(self):
        """测试无效目录"""
        with pytest.raises(ValueError, match="does not exist"):
            self.engine.find_in_files("/nonexistent/path", "test")
    
    def test_find_in_files_not_directory(self):
        """测试路径不是目录"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with pytest.raises(ValueError, match="not a directory"):
                self.engine.find_in_files(tmp_path, "test")
        finally:
            os.unlink(tmp_path)
    
    def test_file_pattern_matching(self):
        """测试文件模式匹配"""
        engine = SearchEngine()
        
        # 测试通配符
        assert engine._matches_file_pattern("test.py", ["*.py"])
        assert engine._matches_file_pattern("test.txt", ["*.txt"])
        assert not engine._matches_file_pattern("test.py", ["*.txt"])
        
        # 测试多个模式
        assert engine._matches_file_pattern("test.py", ["*.py", "*.txt"])
        assert engine._matches_file_pattern("test.txt", ["*.py", "*.txt"])
        
        # 测试 * 匹配所有
        assert engine._matches_file_pattern("anything.xyz", ["*"])
    
    def test_multiline_search(self):
        """测试多行文本搜索"""
        text = "Line 1\nLine 2\nLine 3\nLine 2 again"
        matches = self.engine.find_in_text(text, "Line 2")
        
        assert len(matches) == 2
        assert matches[0].line_number == 2
        assert matches[1].line_number == 4
    
    def test_special_characters(self):
        """测试特殊字符搜索"""
        text = "Price: $100\nDiscount: 50%"
        
        # 普通搜索应该能找到特殊字符
        matches = self.engine.find_in_text(text, "$100")
        assert len(matches) == 1
        
        matches = self.engine.find_in_text(text, "50%")
        assert len(matches) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
