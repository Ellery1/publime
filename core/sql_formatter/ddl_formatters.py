"""
SQL格式化器DDL格式化模块

包含CREATE TABLE、CREATE VIEW、CREATE INDEX等DDL语句格式化函数
"""

import re
from .parser import split_columns


def format_create_table(statement: str) -> str:
    """格式化 CREATE TABLE 语句"""
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 找到第一个左括号的位置
    open_paren_pos = statement.find('(')
    if open_paren_pos == -1:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    # 提取 CREATE TABLE 部分（包括表名）
    create_table_part = statement[:open_paren_pos].strip()
    
    # 提取列定义部分
    columns_part = statement[open_paren_pos+1:]
    
    # 移除所有换行，变成一行
    columns_part = ' '.join(columns_part.split())
    
    # 找到对应的右括号
    depth = 1
    close_paren_pos = -1
    for i, char in enumerate(columns_part):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                close_paren_pos = i
                break
    
    if close_paren_pos == -1:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    # 提取列定义
    columns_def = columns_part[:close_paren_pos].strip()
    
    # 分割列定义
    columns = split_columns(columns_def)
    
    # 构建结果 - CREATE TABLE 和表名在同一行，列定义缩进2个空格
    result_lines = [f'{create_table_part} (']
    
    for i, col in enumerate(columns):
        if i < len(columns) - 1:
            result_lines.append(f'  {col},')
        else:
            result_lines.append(f'  {col}')
    
    result_lines.append(');')
    
    return '\n'.join(result_lines)


def format_create_view(statement: str) -> str:
    """格式化 CREATE VIEW 语句"""
    # 移除所有注释（包括前导注释和行内注释）
    lines = statement.split('\n')
    clean_lines = []
    
    for line in lines:
        # 移除行内注释
        comment_pos = line.find('--')
        if comment_pos != -1:
            line = line[:comment_pos]
        if line.strip():
            clean_lines.append(line)
    
    # 重新组合SQL
    statement = ' '.join(clean_lines)
    
    # 移除所有多余的空白字符
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取视图名和 SELECT 语句，只匹配到第一个分号为止
    match = re.search(r'CREATE\s+VIEW\s+(\w+)\s+AS\s+(SELECT.*?)(?=;|$)', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    view_name = match.group(1)
    select_statement = match.group(2)
    
    # 避免循环导入
    from .formatters import format_select
    # 格式化 SELECT 语句
    formatted_select = format_select(select_statement)
    
    # 构建结果
    result = f'CREATE VIEW {view_name} AS\n{formatted_select}'
    
    # 确保以分号结尾
    if not result.endswith(';'):
        result += ';'
    
    return result


def format_create_index(statement: str) -> str:
    """格式化 CREATE INDEX 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 确保以分号结尾
    if not statement.endswith(';'):
        statement += ';'
    
    return statement


def format_create_database(statement: str) -> str:
    """格式化 CREATE DATABASE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 确保以分号结尾
    if not statement.endswith(';'):
        statement += ';'
    
    return statement


def format_use(statement: str) -> str:
    """格式化 USE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 确保以分号结尾
    if not statement.endswith(';'):
        statement += ';'
    
    return statement
