"""
搜索引擎模块

提供文件内和跨文件的搜索和替换功能。
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import os


@dataclass
class Match:
    """搜索匹配结果"""
    line_number: int  # 行号（从1开始）
    column: int  # 列号（从0开始）
    matched_text: str  # 匹配的文本
    line_content: str  # 整行内容
    start_pos: int  # 在整个文本中的起始位置
    end_pos: int  # 在整个文本中的结束位置


class SearchEngine:
    """搜索引擎类，处理文本搜索和替换"""
    
    def __init__(self):
        """初始化搜索引擎"""
        pass
    
    def find_in_text(
        self, 
        text: str, 
        pattern: str, 
        case_sensitive: bool = False,
        regex: bool = False
    ) -> List[Match]:
        """
        在文本中查找所有匹配项
        
        Args:
            text: 要搜索的文本
            pattern: 搜索模式
            case_sensitive: 是否大小写敏感
            regex: 是否使用正则表达式
            
        Returns:
            匹配项列表
        """
        if not pattern:
            return []
        
        matches = []
        
        try:
            if regex:
                # 正则表达式搜索
                flags = 0 if case_sensitive else re.IGNORECASE
                regex_pattern = re.compile(pattern, flags)
                
                # 按行处理以获取行号和列号
                lines = text.split('\n')
                current_pos = 0
                
                for line_num, line in enumerate(lines, start=1):
                    for match in regex_pattern.finditer(line):
                        matches.append(Match(
                            line_number=line_num,
                            column=match.start(),
                            matched_text=match.group(),
                            line_content=line,
                            start_pos=current_pos + match.start(),
                            end_pos=current_pos + match.end()
                        ))
                    current_pos += len(line) + 1  # +1 for newline
            else:
                # 普通文本搜索
                search_text = text if case_sensitive else text.lower()
                search_pattern = pattern if case_sensitive else pattern.lower()
                
                lines = text.split('\n')
                current_pos = 0
                
                for line_num, line in enumerate(lines, start=1):
                    search_line = line if case_sensitive else line.lower()
                    start = 0
                    
                    while True:
                        pos = search_line.find(search_pattern, start)
                        if pos == -1:
                            break
                        
                        matches.append(Match(
                            line_number=line_num,
                            column=pos,
                            matched_text=line[pos:pos + len(pattern)],
                            line_content=line,
                            start_pos=current_pos + pos,
                            end_pos=current_pos + pos + len(pattern)
                        ))
                        start = pos + 1
                    
                    current_pos += len(line) + 1  # +1 for newline
        
        except re.error as e:
            # 正则表达式错误
            raise ValueError(f"Invalid regular expression: {e}")
        
        return matches
    
    def replace_in_text(
        self,
        text: str,
        pattern: str,
        replacement: str,
        case_sensitive: bool = False,
        regex: bool = False,
        replace_all: bool = False
    ) -> Tuple[str, int]:
        """
        替换文本
        
        Args:
            text: 原始文本
            pattern: 搜索模式
            replacement: 替换文本
            case_sensitive: 是否大小写敏感
            regex: 是否使用正则表达式
            replace_all: 是否替换所有匹配项（False则只替换第一个）
            
        Returns:
            (新文本, 替换次数)
        """
        if not pattern:
            return text, 0
        
        try:
            if regex:
                # 正则表达式替换
                flags = 0 if case_sensitive else re.IGNORECASE
                count = 0 if replace_all else 1
                new_text, num_replacements = re.subn(
                    pattern, replacement, text, count=count, flags=flags
                )
                return new_text, num_replacements
            else:
                # 普通文本替换
                if replace_all:
                    if case_sensitive:
                        count = text.count(pattern)
                        new_text = text.replace(pattern, replacement)
                    else:
                        # 大小写不敏感的全部替换
                        count = 0
                        result = []
                        search_text = text.lower()
                        search_pattern = pattern.lower()
                        last_end = 0
                        
                        while True:
                            pos = search_text.find(search_pattern, last_end)
                            if pos == -1:
                                result.append(text[last_end:])
                                break
                            
                            result.append(text[last_end:pos])
                            result.append(replacement)
                            count += 1
                            last_end = pos + len(pattern)
                        
                        new_text = ''.join(result)
                    
                    return new_text, count
                else:
                    # 只替换第一个
                    if case_sensitive:
                        pos = text.find(pattern)
                    else:
                        pos = text.lower().find(pattern.lower())
                    
                    if pos == -1:
                        return text, 0
                    
                    new_text = text[:pos] + replacement + text[pos + len(pattern):]
                    return new_text, 1
        
        except re.error as e:
            raise ValueError(f"Invalid regular expression: {e}")
    
    def find_in_files(
        self,
        directory: str,
        pattern: str,
        file_patterns: Optional[List[str]] = None,
        case_sensitive: bool = False,
        regex: bool = False
    ) -> Dict[str, List[Match]]:
        """
        在多个文件中搜索
        
        Args:
            directory: 搜索目录
            pattern: 搜索模式
            file_patterns: 文件类型过滤器（如 ['*.py', '*.txt']）
            case_sensitive: 是否大小写敏感
            regex: 是否使用正则表达式
            
        Returns:
            字典，键为文件路径，值为匹配项列表
        """
        if not os.path.exists(directory):
            raise ValueError(f"Directory does not exist: {directory}")
        
        if not os.path.isdir(directory):
            raise ValueError(f"Path is not a directory: {directory}")
        
        results = {}
        
        # 如果没有指定文件模式，默认搜索所有文本文件
        if file_patterns is None:
            file_patterns = ['*']
        
        # 遍历目录
        for root, dirs, files in os.walk(directory):
            for filename in files:
                # 检查文件是否匹配过滤器
                if not self._matches_file_pattern(filename, file_patterns):
                    continue
                
                file_path = os.path.join(root, filename)
                
                try:
                    # 尝试读取文件
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 搜索文件内容
                    matches = self.find_in_text(content, pattern, case_sensitive, regex)
                    
                    if matches:
                        results[file_path] = matches
                
                except (IOError, OSError):
                    # 跳过无法读取的文件
                    continue
        
        return results
    
    def _matches_file_pattern(self, filename: str, patterns: List[str]) -> bool:
        """
        检查文件名是否匹配任一模式
        
        Args:
            filename: 文件名
            patterns: 模式列表（支持通配符 * 和 ?）
            
        Returns:
            是否匹配
        """
        if '*' in patterns:
            return True
        
        for pattern in patterns:
            # 将通配符模式转换为正则表达式
            regex_pattern = pattern.replace('.', r'\.')
            regex_pattern = regex_pattern.replace('*', '.*')
            regex_pattern = regex_pattern.replace('?', '.')
            regex_pattern = f'^{regex_pattern}$'
            
            if re.match(regex_pattern, filename, re.IGNORECASE):
                return True
        
        return False
