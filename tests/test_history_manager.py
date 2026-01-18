"""
历史记录管理器单元测试
"""

import pytest
import tempfile
import os
import json
from core.history_manager import HistoryManager, HistoryEntry
from datetime import datetime


class TestHistoryManager:
    """历史记录管理器测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.manager = HistoryManager(max_items=5)
        # 使用临时文件作为历史记录文件
        self.temp_history_file = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.json'
        )
        self.temp_history_file.close()
        self.manager.history_file = self.temp_history_file.name
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        if os.path.exists(self.temp_history_file.name):
            os.unlink(self.temp_history_file.name)
    
    def test_manager_creation(self):
        """测试管理器创建"""
        manager = HistoryManager()
        assert manager.max_items == 20
        assert len(manager.history) == 0
    
    def test_add_file(self):
        """测试添加文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            self.manager.add_file(tmp_path)
            
            assert self.manager.get_history_size() == 1
            assert self.manager.is_in_history(tmp_path)
            
            recent = self.manager.get_recent_files()
            assert len(recent) == 1
            assert os.path.abspath(tmp_path) == recent[0]
        finally:
            os.unlink(tmp_path)
    
    def test_add_multiple_files(self):
        """测试添加多个文件"""
        files = []
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            files.append(tmp.name)
            self.manager.add_file(tmp.name)
        
        try:
            assert self.manager.get_history_size() == 3
            
            recent = self.manager.get_recent_files()
            # 应该按添加顺序倒序排列（最新的在前）
            assert os.path.abspath(files[2]) == recent[0]
            assert os.path.abspath(files[1]) == recent[1]
            assert os.path.abspath(files[0]) == recent[2]
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)
    
    def test_add_duplicate_file(self):
        """测试添加重复文件"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # 添加两次
            self.manager.add_file(tmp_path)
            self.manager.add_file(tmp_path)
            
            # 应该只有一个条目
            assert self.manager.get_history_size() == 1
        finally:
            os.unlink(tmp_path)
    
    def test_max_items_limit(self):
        """测试最大数量限制"""
        files = []
        # 添加超过最大数量的文件
        for i in range(7):
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            files.append(tmp.name)
            self.manager.add_file(tmp.name)
        
        try:
            # 应该只保留最近的5个
            assert self.manager.get_history_size() == 5
            
            recent = self.manager.get_recent_files()
            # 最早的两个应该被移除
            assert os.path.abspath(files[0]) not in recent
            assert os.path.abspath(files[1]) not in recent
            # 最新的5个应该保留
            assert os.path.abspath(files[6]) in recent
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)
    
    def test_time_ordering(self):
        """测试时间排序"""
        files = []
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            files.append(tmp.name)
            self.manager.add_file(tmp.name)
        
        try:
            # 重新打开第一个文件
            self.manager.add_file(files[0])
            
            recent = self.manager.get_recent_files()
            # 第一个文件应该移到最前面
            assert os.path.abspath(files[0]) == recent[0]
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)
    
    def test_clear_history(self):
        """测试清空历史记录"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            self.manager.add_file(tmp_path)
            assert self.manager.get_history_size() == 1
            
            self.manager.clear_history()
            assert self.manager.get_history_size() == 0
        finally:
            os.unlink(tmp_path)
    
    def test_remove_file(self):
        """测试移除文件"""
        files = []
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            files.append(tmp.name)
            self.manager.add_file(tmp.name)
        
        try:
            # 移除中间的文件
            self.manager.remove_file(files[1])
            
            assert self.manager.get_history_size() == 2
            assert not self.manager.is_in_history(files[1])
            assert self.manager.is_in_history(files[0])
            assert self.manager.is_in_history(files[2])
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)
    
    def test_save_and_load(self):
        """测试保存和加载"""
        files = []
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            files.append(tmp.name)
            self.manager.add_file(tmp.name)
        
        try:
            # 保存
            self.manager.save_to_disk()
            
            # 创建新管理器并加载
            new_manager = HistoryManager()
            new_manager.history_file = self.manager.history_file
            new_manager.load_from_disk()
            
            # 验证数据一致
            assert new_manager.get_history_size() == 3
            
            original_files = self.manager.get_recent_files()
            loaded_files = new_manager.get_recent_files()
            assert original_files == loaded_files
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)
    
    def test_load_nonexistent_file(self):
        """测试加载不存在的历史文件"""
        manager = HistoryManager()
        manager.history_file = "/nonexistent/path/history.json"
        
        # 应该不会崩溃
        manager.load_from_disk()
        assert manager.get_history_size() == 0
    
    def test_file_exists_status(self):
        """测试文件存在状态"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        self.manager.add_file(tmp_path)
        
        # 文件存在
        entries = self.manager.get_recent_entries()
        assert entries[0].exists is True
        
        # 删除文件
        os.unlink(tmp_path)
        
        # 再次获取，状态应该更新
        entries = self.manager.get_recent_entries()
        assert entries[0].exists is False
    
    def test_empty_file_path(self):
        """测试空文件路径"""
        self.manager.add_file("")
        assert self.manager.get_history_size() == 0
        
        self.manager.add_file(None)
        assert self.manager.get_history_size() == 0
    
    def test_history_entry_serialization(self):
        """测试历史记录条目序列化"""
        entry = HistoryEntry(
            file_path="/test/path.txt",
            last_opened=datetime.now().isoformat(),
            exists=True
        )
        
        # 转换为字典
        data = entry.to_dict()
        assert data['file_path'] == "/test/path.txt"
        assert 'last_opened' in data
        assert data['exists'] is True
        
        # 从字典创建
        new_entry = HistoryEntry.from_dict(data)
        assert new_entry.file_path == entry.file_path
        assert new_entry.last_opened == entry.last_opened
        assert new_entry.exists == entry.exists
    
    def test_path_normalization(self):
        """测试路径规范化"""
        # 使用相对路径（在当前目录创建）
        import tempfile
        # 在当前目录创建临时文件以避免跨驱动器问题
        tmp_dir = os.path.join(os.getcwd(), 'temp_test')
        os.makedirs(tmp_dir, exist_ok=True)
        
        try:
            tmp_path = os.path.join(tmp_dir, 'test_file.txt')
            with open(tmp_path, 'w') as f:
                f.write('test')
            
            # 获取相对路径
            rel_path = os.path.relpath(tmp_path)
            
            self.manager.add_file(rel_path)
            
            # 应该存储为绝对路径
            recent = self.manager.get_recent_files()
            assert os.path.isabs(recent[0])
            assert os.path.abspath(rel_path) == recent[0]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(tmp_dir):
                os.rmdir(tmp_dir)
    
    def test_save_with_invalid_path(self):
        """测试保存到无效路径"""
        self.manager.history_file = "/invalid/path/history.json"
        
        # 应该不会崩溃
        self.manager.save_to_disk()
    
    def test_load_corrupted_file(self):
        """测试加载损坏的历史文件"""
        # 写入无效的JSON
        with open(self.manager.history_file, 'w') as f:
            f.write("invalid json {")
        
        # 应该不会崩溃
        self.manager.load_from_disk()
        assert self.manager.get_history_size() == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
