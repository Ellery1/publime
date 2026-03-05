"""
语言检测器模块

该模块实现了基于文件扩展名和内容的编程语言检测功能。
"""

import os
import re
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
    
    @staticmethod
    def detect_language_from_content(content: str) -> Optional[str]:
        """
        根据内容检测编程语言
        
        Args:
            content: 文本内容
            
        Returns:
            Optional[str]: 检测到的语言名称，如果无法检测或内容模糊则返回 None
        """
        try:
            if not content or not content.strip():
                return None
            
            # 转换为小写以便不区分大小写匹配
            content_lower = content.lower()
            content_upper = content.upper()
            
            # SQL 检测 - 检查常见SQL关键字
            sql_keywords = [
                r'\bselect\b.*\bfrom\b',
                r'\binsert\s+into\b',
                r'\bupdate\b.*\bset\b',
                r'\bdelete\s+from\b',
                r'\bcreate\s+(table|view|database|index)\b',
                r'\balter\s+table\b',
                r'\bdrop\s+(table|view|database)\b',
                r'\bwhere\b',  # WHERE子句
                r'\bjoin\b',   # JOIN
                r'\bgroup\s+by\b',  # GROUP BY
                r'\border\s+by\b',  # ORDER BY
            ]
            sql_score = sum(1 for pattern in sql_keywords if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL))
            
            # Python 检测 - 检查Python特有语法
            python_patterns = [
                r'\bdef\s+\w+\s*\(',
                r'\bclass\s+\w+',
                r'\bimport\s+\w+',
                r'\bfrom\s+\w+\s+import\b',
                r'^\s*#.*python',  # 注释中提到python
                r'\bif\s+__name__\s*==\s*["\']__main__["\']',
            ]
            python_score = sum(1 for pattern in python_patterns if re.search(pattern, content, re.MULTILINE))
            
            # Java 检测 - 检查Java特有语法
            java_patterns = [
                r'\bpublic\s+class\s+\w+',
                r'\bprivate\s+(static\s+)?(void|int|String|boolean)',
                r'\bprotected\s+',
                r'\bpublic\s+static\s+void\s+main',
                r'\bSystem\.out\.println',
            ]
            java_score = sum(1 for pattern in java_patterns if re.search(pattern, content))
            
            # JavaScript 检测 - 检查JavaScript特有语法
            js_patterns = [
                r'\bfunction\s+\w+\s*\(',
                r'\bconst\s+\w+\s*=',
                r'\blet\s+\w+\s*=',
                r'\bvar\s+\w+\s*=',
                r'=>',  # 箭头函数
                r'\bconsole\.log',
            ]
            js_score = sum(1 for pattern in js_patterns if re.search(pattern, content))
            
            # JSON 检测 - 检查JSON格式
            json_score = 0
            stripped = content.strip()
            if (stripped.startswith('{') and stripped.endswith('}')) or \
               (stripped.startswith('[') and stripped.endswith(']')):
                # 检查是否包含键值对格式
                if re.search(r'"\w+":\s*["\[\{]', content):
                    json_score = 3
            
            # 收集所有得分
            scores = {
                'sql': sql_score,
                'python': python_score,
                'java': java_score,
                'javascript': js_score,
                'json': json_score,
            }
            
            # 找到最高分
            max_score = max(scores.values())
            
            # 如果最高分为0，无法检测
            if max_score == 0:
                return None
            
            # 如果最高分为1且不是JSON，置信度太低
            if max_score == 1 and scores['json'] != max_score:
                return None
            
            # 返回得分最高的语言
            for lang, score in scores.items():
                if score == max_score:
                    return lang
            
            return None
        except Exception as e:
            # 检测失败,返回None
            print(f"Language detection error: {e}")
            return None
