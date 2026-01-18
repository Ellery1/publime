"""
文件管理器模块

处理文件读写操作，支持编码检测和大文件处理。
"""

import os
import chardet
from typing import Optional


class FileManager:
    """
    文件管理器类
    
    提供文件读取、写入、编码检测和大文件检测功能。
    支持多种编码格式的自动检测。
    """
    
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """
        检测文件编码
        
        使用 chardet 库检测文件的字符编码。
        如果检测失败，默认返回 'utf-8'。
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 检测到的编码名称（如 'utf-8', 'gbk' 等）
            
        Raises:
            FileNotFoundError: 如果文件不存在
            PermissionError: 如果没有读取权限
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"没有读取权限: {file_path}")
        
        try:
            # 读取文件的前几个字节来检测编码
            with open(file_path, 'rb') as f:
                raw_data = f.read(min(10000, os.path.getsize(file_path)))
            
            # 使用 chardet 检测编码
            result = chardet.detect(raw_data)
            encoding = result.get('encoding')
            
            # 如果检测到的编码为 None 或置信度太低，使用默认编码
            if encoding is None or result.get('confidence', 0) < 0.7:
                return 'utf-8'
            
            return encoding
        except Exception:
            # 如果检测失败，返回默认编码
            return 'utf-8'
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        读取文件内容
        
        自动检测文件编码并读取内容。
        如果使用检测到的编码失败，会尝试常见的编码格式。
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容
            
        Raises:
            FileNotFoundError: 如果文件不存在
            PermissionError: 如果没有读取权限
            UnicodeDecodeError: 如果所有编码尝试都失败
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"没有读取权限: {file_path}")
        
        # 首先尝试检测到的编码
        detected_encoding = FileManager.detect_encoding(file_path)
        
        # 尝试的编码列表（按优先级排序）
        encodings_to_try = [detected_encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1']
        
        # 去重，保持顺序
        seen = set()
        encodings_to_try = [x for x in encodings_to_try if not (x in seen or seen.add(x))]
        
        last_error = None
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                continue
        
        # 如果所有编码都失败，抛出最后一个错误
        raise UnicodeDecodeError(
            'unknown', b'', 0, 1,
            f"无法使用任何编码读取文件: {file_path}. 尝试的编码: {encodings_to_try}"
        )
    
    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        写入文件内容
        
        将内容写入指定文件。如果文件不存在会创建新文件。
        如果目录不存在会创建目录。
        
        Args:
            file_path: 文件路径
            content: 要写入的内容
            encoding: 文件编码，默认为 'utf-8'
            
        Returns:
            bool: 写入成功返回 True，失败返回 False
            
        Raises:
            PermissionError: 如果没有写入权限
            OSError: 如果磁盘空间不足或其他 IO 错误
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # 检查是否有写入权限（如果文件已存在）
            if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
                raise PermissionError(f"没有写入权限: {file_path}")
            
            # 写入文件
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return True
        except (PermissionError, OSError) as e:
            # 重新抛出异常，让调用者处理
            raise
        except Exception as e:
            # 其他未预期的错误
            raise OSError(f"写入文件失败: {file_path}. 错误: {str(e)}")
    
    @staticmethod
    def is_large_file(file_path: str, threshold_mb: int = 10) -> bool:
        """
        检查是否为大文件
        
        根据指定的阈值判断文件是否为大文件。
        
        Args:
            file_path: 文件路径
            threshold_mb: 大文件阈值（MB），默认为 10MB
            
        Returns:
            bool: 如果文件大小超过阈值返回 True，否则返回 False
            
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        return file_size_mb > threshold_mb
