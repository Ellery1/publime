"""
语言检测器模块

该模块实现了基于文件扩展名的编程语言检测功能。
"""

import os
from typing import Optional


class LanguageDetector:
    """
    语言检测器类
    
    根据文件扩展名检测编程语言类型。
    """
    
    # 文件扩展名到语言的映射
    EXTENSION_MAP = {
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyi': 'python',
        
        # Java
        '.java': 'java',
        
        # SQL
        '.sql': 'sql',
        
        # JSON
        '.json': 'json',
        
        # JavaScript
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        
        # Kotlin
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        
        # Markdown
        '.md': 'markdown',
        '.markdown': 'markdown',
        
        # XML
        '.xml': 'xml',
        
        # YAML
        '.yaml': 'yaml',
        '.yml': 'yaml',
    }
    
    @staticmethod
    def detect_language(file_path: str) -> Optional[str]:
        """
        根据文件路径检测编程语言
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 检测到的语言名称（python, java, sql, json, javascript, kotlin），
                          如果无法检测则返回 None
        """
        if not file_path:
            return None
        
        # 获取文件扩展名（转换为小写）
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # 查找对应的语言
        return LanguageDetector.EXTENSION_MAP.get(ext)
    
    @staticmethod
    def get_supported_extensions() -> list[str]:
        """
        获取所有支持的文件扩展名列表
        
        Returns:
            list[str]: 支持的文件扩展名列表
        """
        return list(LanguageDetector.EXTENSION_MAP.keys())
    
    @staticmethod
    def get_supported_languages() -> list[str]:
        """
        获取所有支持的编程语言列表
        
        Returns:
            list[str]: 支持的编程语言列表（去重）
        """
        return list(set(LanguageDetector.EXTENSION_MAP.values()))
    
    @staticmethod
    def is_supported(file_path: str) -> bool:
        """
        检查文件是否支持语法高亮
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 如果文件扩展名被支持则返回 True，否则返回 False
        """
        return LanguageDetector.detect_language(file_path) is not None
