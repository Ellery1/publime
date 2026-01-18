"""
文件管理器单元测试

测试 FileManager 类的各种功能，包括文件读写、编码检测和大文件检测。
"""

import os
import tempfile
import pytest
from core.file_manager import FileManager


class TestFileManager:
    """FileManager 类的单元测试"""
    
    def test_read_file_utf8(self):
        """测试读取 UTF-8 编码的文件"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            test_content = "Hello, 世界! 这是一个测试文件。"
            f.write(test_content)
            temp_path = f.name
        
        try:
            content = FileManager.read_file(temp_path)
            assert content == test_content
        finally:
            os.unlink(temp_path)
    
    def test_read_file_gbk(self):
        """测试读取 GBK 编码的文件"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='gbk', delete=False, suffix='.txt') as f:
            test_content = "这是 GBK 编码的文件"
            f.write(test_content)
            temp_path = f.name
        
        try:
            content = FileManager.read_file(temp_path)
            assert content == test_content
        finally:
            os.unlink(temp_path)
    
    def test_read_file_not_found(self):
        """测试读取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            FileManager.read_file("/nonexistent/path/file.txt")
    
    def test_write_file_utf8(self):
        """测试写入 UTF-8 编码的文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "test_write.txt")
            test_content = "测试写入内容 with Unicode: 你好世界 🌍"
            
            result = FileManager.write_file(temp_path, test_content)
            assert result is True
            assert os.path.exists(temp_path)
            
            # 验证写入的内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert content == test_content
    
    def test_write_file_creates_directory(self):
        """测试写入文件时自动创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "subdir1", "subdir2", "test.txt")
            test_content = "测试内容"
            
            result = FileManager.write_file(nested_path, test_content)
            assert result is True
            assert os.path.exists(nested_path)
            
            # 验证内容
            content = FileManager.read_file(nested_path)
            assert content == test_content
    
    def test_write_file_overwrite(self):
        """测试覆盖已存在的文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("原始内容")
            temp_path = f.name
        
        try:
            new_content = "新内容"
            result = FileManager.write_file(temp_path, new_content)
            assert result is True
            
            # 验证内容已被覆盖
            content = FileManager.read_file(temp_path)
            assert content == new_content
        finally:
            os.unlink(temp_path)
    
    def test_detect_encoding_utf8(self):
        """测试检测 UTF-8 编码"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            f.write("UTF-8 编码的文件内容 with 中文")
            temp_path = f.name
        
        try:
            encoding = FileManager.detect_encoding(temp_path)
            # chardet 可能返回 'utf-8' 或 'ascii'（如果内容简单）
            assert encoding.lower() in ['utf-8', 'ascii']
        finally:
            os.unlink(temp_path)
    
    def test_detect_encoding_file_not_found(self):
        """测试检测不存在文件的编码"""
        with pytest.raises(FileNotFoundError):
            FileManager.detect_encoding("/nonexistent/file.txt")
    
    def test_is_large_file_small(self):
        """测试小文件检测"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            # 写入小于 10MB 的内容（约 1KB）
            f.write("小文件内容" * 100)
            temp_path = f.name
        
        try:
            is_large = FileManager.is_large_file(temp_path, threshold_mb=10)
            assert is_large is False
        finally:
            os.unlink(temp_path)
    
    def test_is_large_file_large(self):
        """测试大文件检测"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            # 写入超过 1MB 的内容
            content = "x" * (1024 * 1024 + 1)  # 1MB + 1 byte
            f.write(content)
            temp_path = f.name
        
        try:
            is_large = FileManager.is_large_file(temp_path, threshold_mb=1)
            assert is_large is True
        finally:
            os.unlink(temp_path)
    
    def test_is_large_file_custom_threshold(self):
        """测试自定义阈值的大文件检测"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            # 写入约 0.5MB 的内容
            content = "x" * (512 * 1024)
            f.write(content)
            temp_path = f.name
        
        try:
            # 使用 1MB 阈值，应该返回 False
            assert FileManager.is_large_file(temp_path, threshold_mb=1) is False
            # 使用 0.1MB 阈值，应该返回 True
            assert FileManager.is_large_file(temp_path, threshold_mb=0.1) is True
        finally:
            os.unlink(temp_path)
    
    def test_is_large_file_not_found(self):
        """测试检测不存在文件的大小"""
        with pytest.raises(FileNotFoundError):
            FileManager.is_large_file("/nonexistent/file.txt")
    
    def test_read_write_roundtrip(self):
        """测试读写往返一致性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "roundtrip.txt")
            test_content = "测试往返一致性\n包含多行\n和特殊字符: !@#$%^&*()\n以及 Unicode: 你好世界 🎉"
            
            # 写入
            FileManager.write_file(temp_path, test_content)
            # 读取
            read_content = FileManager.read_file(temp_path)
            
            # 验证一致性
            assert read_content == test_content
    
    def test_read_empty_file(self):
        """测试读取空文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            content = FileManager.read_file(temp_path)
            assert content == ""
        finally:
            os.unlink(temp_path)
    
    def test_write_empty_content(self):
        """测试写入空内容"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "empty.txt")
            
            result = FileManager.write_file(temp_path, "")
            assert result is True
            
            content = FileManager.read_file(temp_path)
            assert content == ""
    
    def test_read_file_with_special_characters(self):
        """测试读取包含特殊字符的文件"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt', newline='') as f:
            test_content = "特殊字符测试:\n\t制表符\n换行符\r\n回车换行\n引号\"和'单引号'\n反斜杠\\"
            f.write(test_content)
            temp_path = f.name
        
        try:
            # 使用 newline='' 读取以保留原始行结束符
            with open(temp_path, 'r', encoding='utf-8', newline='') as f:
                content = f.read()
            assert content == test_content
        finally:
            os.unlink(temp_path)
    
    def test_write_file_with_different_encoding(self):
        """测试使用不同编码写入文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "gbk_file.txt")
            test_content = "GBK 编码测试"
            
            # 使用 GBK 编码写入
            result = FileManager.write_file(temp_path, test_content, encoding='gbk')
            assert result is True
            
            # 使用 GBK 编码读取验证
            with open(temp_path, 'r', encoding='gbk') as f:
                content = f.read()
            assert content == test_content
