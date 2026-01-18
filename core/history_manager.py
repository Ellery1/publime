"""
历史记录管理器模块

管理最近打开文件的历史记录。
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
from pathlib import Path


@dataclass
class HistoryEntry:
    """历史记录条目"""
    file_path: str
    last_opened: str  # ISO格式的时间字符串
    exists: bool  # 文件是否仍然存在
    
    def to_dict(self):
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建"""
        return cls(**data)


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, max_items: int = 20):
        """
        初始化历史记录管理器
        
        Args:
            max_items: 最大历史记录数量
        """
        self.max_items = max_items
        self.history: List[HistoryEntry] = []
        self.history_file = self._get_history_file_path()
    
    def _get_history_file_path(self) -> str:
        """获取历史记录文件路径"""
        # 使用用户主目录下的 .publime 文件夹
        home = Path.home()
        config_dir = home / '.publime'
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / 'history.json')
    
    def add_file(self, file_path: str) -> None:
        """
        添加文件到历史记录
        
        Args:
            file_path: 文件路径
        """
        if not file_path:
            return
        
        # 规范化路径
        file_path = os.path.abspath(file_path)
        
        # 检查文件是否存在
        exists = os.path.exists(file_path)
        
        # 移除已存在的相同路径
        self.history = [entry for entry in self.history if entry.file_path != file_path]
        
        # 添加到开头
        entry = HistoryEntry(
            file_path=file_path,
            last_opened=datetime.now().isoformat(),
            exists=exists
        )
        self.history.insert(0, entry)
        
        # 限制数量
        if len(self.history) > self.max_items:
            self.history = self.history[:self.max_items]
    
    def get_recent_files(self) -> List[str]:
        """
        获取最近文件列表
        
        Returns:
            文件路径列表，按时间倒序排列
        """
        # 更新文件存在状态
        for entry in self.history:
            entry.exists = os.path.exists(entry.file_path)
        
        return [entry.file_path for entry in self.history]
    
    def get_recent_entries(self) -> List[HistoryEntry]:
        """
        获取最近文件条目列表（包含完整信息）
        
        Returns:
            历史记录条目列表
        """
        # 更新文件存在状态
        for entry in self.history:
            entry.exists = os.path.exists(entry.file_path)
        
        return self.history.copy()
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.history = []
    
    def remove_file(self, file_path: str) -> None:
        """
        从历史记录中移除文件
        
        Args:
            file_path: 文件路径
        """
        file_path = os.path.abspath(file_path)
        self.history = [entry for entry in self.history if entry.file_path != file_path]
    
    def save_to_disk(self) -> None:
        """保存历史记录到磁盘"""
        try:
            data = {
                'max_items': self.max_items,
                'history': [entry.to_dict() for entry in self.history]
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except (IOError, OSError) as e:
            # 保存失败时静默处理，不影响程序运行
            print(f"Warning: Failed to save history: {e}")
    
    def load_from_disk(self) -> None:
        """从磁盘加载历史记录"""
        if not os.path.exists(self.history_file):
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.max_items = data.get('max_items', 20)
            history_data = data.get('history', [])
            
            self.history = [HistoryEntry.from_dict(entry) for entry in history_data]
            
            # 更新文件存在状态
            for entry in self.history:
                entry.exists = os.path.exists(entry.file_path)
        
        except (IOError, OSError, json.JSONDecodeError) as e:
            # 加载失败时静默处理，使用空历史记录
            print(f"Warning: Failed to load history: {e}")
            self.history = []
    
    def get_history_size(self) -> int:
        """
        获取历史记录数量
        
        Returns:
            历史记录数量
        """
        return len(self.history)
    
    def is_in_history(self, file_path: str) -> bool:
        """
        检查文件是否在历史记录中
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否在历史记录中
        """
        file_path = os.path.abspath(file_path)
        return any(entry.file_path == file_path for entry in self.history)
