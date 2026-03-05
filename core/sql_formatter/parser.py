"""
SQL格式化器解析模块

包含SQL语句解析相关的函数
"""

import re
from typing import List


def split_statements(text: str) -> List[str]:
    """
    按分号分割SQL语句,保留UNION ALL
    
    Args:
        text: SQL文本
        
    Returns:
        语句列表
    """
    # 首先按分号分割语句
    statements = []
    current = ''
    depth = 0
    in_string = False
    string_char = None
    in_comment = False
    
    i = 0
    while i < len(text):
        char = text[i]
        
        # 处理字符串
        if char in ('"', "'", '`') and (i == 0 or text[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        
        # 不在字符串中时处理括号和注释
        if not in_string:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            # 跟踪注释状态
            elif char == '-' and i + 1 < len(text) and text[i+1] == '-':
                # 跳过注释直到换行
                comment_start = i
                while i < len(text) and text[i] != '\n':
                    i += 1
                # 检查下一行是否是SQL关键字
                j = i + 1
                while j < len(text) and text[j].isspace():
                    j += 1
                if j < len(text):
                    remaining = text[j:].upper()
                    # 检查是否是SQL关键字的开始
                    if remaining.startswith('SELECT ') or remaining.startswith('CREATE ') or \
                       remaining.startswith('UPDATE ') or remaining.startswith('DELETE ') or \
                       remaining.startswith('INSERT ') or remaining.startswith('WITH ') or \
                       remaining.startswith('USE '):
                        # 保存当前语句
                        if current.strip():
                            statements.append(current.strip())
                        # 开始新的语句
                        current = text[comment_start:i+1]
                    else:
                        # 添加注释到current
                        current += text[comment_start:i+1]
                else:
                    # 添加注释到current
                    current += text[comment_start:i+1]
                # 跳过下一个字符（换行符）
                i += 1
                continue
            else:
                current += char
        else:
            current += char
        
        # 只在深度为0且不在字符串中且不在注释中时检查分号
        if char == ';' and depth == 0 and not in_string and not in_comment:
            stmt = current.strip()
            if stmt:
                statements.append(stmt)
            current = ''
        
        i += 1
    
    # 添加最后一个语句(如果没有分号结尾)
    if current.strip():
        # 检查是否包含多个语句（通过关键字检测）
        # 查找主要SQL关键字的位置（只在深度为0时）
        keywords = ['SELECT', 'CREATE', 'UPDATE', 'DELETE', 'INSERT', 'WITH', 'USE']
        positions = []
        
        depth = 0
        in_comment = False
        i = 0
        while i < len(current):
            char = current[i]
            
            # 跟踪括号深度
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            # 跟踪注释状态
            if char == '-' and i + 1 < len(current) and current[i+1] == '-':
                in_comment = True
                # 跳过注释直到换行
                while i < len(current) and current[i] != '\n':
                    i += 1
                # 跳过换行符
                if i < len(current) and current[i] == '\n':
                    i += 1
                # 注释结束，设置in_comment为False
                in_comment = False
                # 检查下一行是否是关键字
                j = i
                # 跳过所有空白字符（包括空行）
                while j < len(current) and current[j].isspace():
                    j += 1
                if j < len(current):
                    # 提取从j开始的内容
                    remaining = current[j:]
                    if remaining:
                        # 检查是否是关键字的开始
                        remaining_upper = remaining.upper()
                        if remaining_upper.startswith('SELECT ') or remaining_upper.startswith('CREATE ') or \
                           remaining_upper.startswith('UPDATE ') or remaining_upper.startswith('DELETE ') or \
                           remaining_upper.startswith('INSERT ') or remaining_upper.startswith('WITH ') or \
                           remaining_upper.startswith('USE '):
                            # 确保不是第一个关键字
                            if i > 0:
                                # 检查该位置是否已经在positions中
                                if not any(pos == i for pos, kw in positions):
                                    positions.append((i, remaining_upper.split()[0]))
                # 跳过当前循环的剩余部分
                continue
            elif char == '\n' and in_comment:
                in_comment = False
            
            # 只在深度为0且不在注释中时检查关键字
            if depth == 0 and not in_comment:
                # 跳过空白字符
                j = i
                while j < len(current) and current[j].isspace():
                    j += 1
                
                if j < len(current):
                    # 检查是否是关键字的开始
                    remaining = current[j:].upper()
                    
                    # 检查是否是另一个 SQL 语句的开始（只在深度为0时）
                    if remaining.startswith('SELECT ') or remaining.startswith('CREATE ') or \
                       remaining.startswith('UPDATE ') or remaining.startswith('DELETE ') or \
                       remaining.startswith('INSERT ') or remaining.startswith('WITH ') or \
                       remaining.startswith('USE '):
                        # 确保不是第一个关键字
                        if i > 0:
                            positions.append((i, remaining.split()[0]))
            
            i += 1
        
        # 按位置排序
        positions.sort()
        
        if positions:
            # 分割成多个语句
            start = 0
            for pos, kw in positions:
                # 提取前一个语句
                stmt = current[start:pos].strip()
                if stmt:
                    statements.append(stmt)
                start = pos
            
            # 提取最后一个语句
            stmt = current[start:].strip()
            if stmt:
                statements.append(stmt)
        else:
            # 只有一个语句
            statements.append(current.strip())
    
    return statements


def parse_select_statement(statement: str) -> dict:
    """
    解析 SELECT 语句，提取各个部分（考虑括号深度）
    
    Args:
        statement: SELECT 语句
        
    Returns:
        包含各部分的字典
    """
    parts = {
        'select': '',
        'from': '',
        'where': '',
        'group_by': '',
        'having': '',
        'order_by': '',
        'limit': ''
    }
    
    # 查找 SELECT 关键字
    select_pos = statement.upper().find('SELECT')
    if select_pos == -1:
        return parts
    
    # 从 SELECT 后开始解析
    i = select_pos + 6  # len('SELECT')
    
    # 跳过空白
    while i < len(statement) and statement[i].isspace():
        i += 1
    
    # 当前正在解析的部分
    current_part = 'select'
    current_content = ''
    depth = 0
    in_string = False
    string_char = ''
    in_backtick = False
    
    while i < len(statement):
        char = statement[i]
        
        # 处理字符串和反引号
        if char in ('"', "'") and not in_backtick:
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
            current_content += char
        elif char == '`' and not in_string:
            in_backtick = not in_backtick
            current_content += char
        # 跟踪括号深度（只在非字符串、非反引号时）
        elif char == '(' and not in_string and not in_backtick:
            depth += 1
            current_content += char
        elif char == ')' and not in_string and not in_backtick:
            depth -= 1
            current_content += char
        elif depth == 0 and not in_string and not in_backtick:
            # 只在深度为 0 时检查关键字
            # 检查是否是关键字的开始
            remaining = statement[i:].upper()
            
            # 检查是否是另一个 SQL 语句的开始（只在深度为0时）
            # 注意：需要检查关键字后面的字符，确保不是标识符的一部分
            # 使用 isalnum() 或 '_' 来判断是否是标识符的一部分
            def is_keyword_boundary(text, keyword_len):
                """检查关键字后面是否是边界（不是标识符的一部分）"""
                if len(text) == keyword_len:
                    return True
                next_char = text[keyword_len]
                # 如果下一个字符是字母、数字或下划线，说明是标识符的一部分
                return not (next_char.isalnum() or next_char == '_')
            
            if remaining.startswith('SELECT') and is_keyword_boundary(remaining, 6) or \
               remaining.startswith('CREATE') and is_keyword_boundary(remaining, 6) or \
               remaining.startswith('UPDATE') and is_keyword_boundary(remaining, 6) or \
               remaining.startswith('DELETE') and is_keyword_boundary(remaining, 6) or \
               remaining.startswith('INSERT') and is_keyword_boundary(remaining, 6) or \
               remaining.startswith('WITH') and is_keyword_boundary(remaining, 4) or \
               remaining.startswith('USE') and is_keyword_boundary(remaining, 3):
                # 遇到新的 SQL 语句，停止解析
                # 但是，如果当前正在解析的是FROM子句，那么这可能是一个子查询，不应该停止解析
                if current_part != 'from':
                    break
            elif remaining.startswith('FROM') and is_keyword_boundary(remaining, 4):
                parts[current_part] = current_content.strip()
                current_part = 'from'
                current_content = ''
                i += 4  # len('FROM')
                continue
            elif remaining.startswith('WHERE') and is_keyword_boundary(remaining, 5):
                parts[current_part] = current_content.strip()
                current_part = 'where'
                current_content = ''
                i += 5  # len('WHERE')
                continue
            elif remaining.startswith('GROUP BY') and is_keyword_boundary(remaining, 8):
                parts[current_part] = current_content.strip()
                current_part = 'group_by'
                current_content = ''
                i += 8  # len('GROUP BY')
                continue
            elif remaining.startswith('HAVING') and is_keyword_boundary(remaining, 6):
                parts[current_part] = current_content.strip()
                current_part = 'having'
                current_content = ''
                i += 6  # len('HAVING')
                continue
            elif remaining.startswith('ORDER BY') and is_keyword_boundary(remaining, 8):
                parts[current_part] = current_content.strip()
                current_part = 'order_by'
                current_content = ''
                i += 8  # len('ORDER BY')
                continue
            elif remaining.startswith('LIMIT') and is_keyword_boundary(remaining, 5):
                parts[current_part] = current_content.strip()
                current_part = 'limit'
                current_content = ''
                i += 5  # len('LIMIT')
                continue
            else:
                current_content += char
        else:
            current_content += char
        
        i += 1
    
    # 保存最后一部分
    if current_content.strip():
        parts[current_part] = current_content.strip()
    
    return parts


def parse_update_statement(statement: str) -> dict:
    """
    解析 UPDATE 语句，提取各个部分（考虑括号深度）
    
    Args:
        statement: UPDATE 语句
        
    Returns:
        包含各部分的字典
    """
    parts = {
        'table': '',
        'set': '',
        'where': ''
    }
    
    # 查找 UPDATE 关键字
    update_pos = statement.upper().find('UPDATE')
    if update_pos == -1:
        return parts
    
    # 从 UPDATE 后开始解析
    i = update_pos + 6  # len('UPDATE')
    
    # 跳过空白
    while i < len(statement) and statement[i].isspace():
        i += 1
    
    # 提取表名
    table_name = ''
    while i < len(statement) and not statement[i].isspace():
        table_name += statement[i]
        i += 1
    parts['table'] = table_name
    
    # 跳过空白
    while i < len(statement) and statement[i].isspace():
        i += 1
    
    # 查找 SET 关键字
    if not statement[i:].upper().startswith('SET'):
        return parts
    
    i += 3  # len('SET')
    
    # 跳过空白
    while i < len(statement) and statement[i].isspace():
        i += 1
    
    # 解析 SET 和 WHERE 部分
    current_part = 'set'
    current_content = ''
    depth = 0
    
    while i < len(statement):
        char = statement[i]
        
        # 跟踪括号深度
        if char == '(':
            depth += 1
            current_content += char
        elif char == ')':
            depth -= 1
            current_content += char
        elif depth == 0:
            # 只在深度为 0 时检查关键字
            remaining = statement[i:].upper()
            if remaining.startswith('WHERE '):
                parts[current_part] = current_content.strip()
                current_part = 'where'
                current_content = ''
                i += 6  # len('WHERE ')
                continue
            else:
                current_content += char
        else:
            current_content += char
        
        i += 1
    
    # 保存最后一部分
    if current_content.strip():
        parts[current_part] = current_content.strip()
    
    return parts


def split_columns(text: str) -> List[str]:
    """
    分割列（考虑括号内的逗号）
    
    Args:
        text: 列文本
        
    Returns:
        列列表
    """
    columns = []
    current = ''
    depth = 0
    
    # 移除所有换行，变成一行
    text = ' '.join(text.split())
    
    for char in text:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            col = current.strip()
            if col:
                columns.append(col)
            current = ''
            continue
        current += char
    
    if current.strip():
        columns.append(current.strip())
    
    return columns


def split_and_conditions(text: str) -> List[str]:
    """
    分割 AND 条件（考虑括号内的 AND），保留注释
    
    Args:
        text: WHERE 或 HAVING 子句文本
        
    Returns:
        条件列表，每个条件可能包含注释（用换行符分隔）
    """
    conditions = []
    current = ''
    depth = 0
    
    i = 0
    while i < len(text):
        char = text[i]
        
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif char == '\n':
            # 保留换行符（用于注释）
            current += char
        elif depth == 0 and text[i:i+5].upper() == ' AND ':
            cond = current.strip()
            if cond:
                conditions.append(cond)
            current = ''
            i += 5
            continue
        else:
            current += char
        
        i += 1
    
    if current.strip():
        conditions.append(current.strip())
    
    return conditions


def split_union_all(text: str) -> List[str]:
    """
    按UNION ALL分割查询(考虑括号深度)
    
    Args:
        text: SQL文本
        
    Returns:
        查询部分列表
    """
    parts = []
    current = ''
    depth = 0
    i = 0
    
    while i < len(text):
        char = text[i]
        
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif depth == 0:
            # 检查是否是UNION ALL - 更宽松的匹配，允许前后没有空格
            remaining = text[i:].upper()
            # 查找 UNION ALL，可能前后有空格或没有空格
            union_match = re.match(r'\s*UNION\s+ALL\s*', remaining, re.IGNORECASE)
            if union_match:
                # 保存当前部分
                part = current.strip()
                if part:
                    parts.append(part)
                current = ''
                # 跳过UNION ALL及其周围的空格
                i += union_match.end()
                continue
            else:
                current += char
        else:
            current += char
        
        i += 1
    
    # 添加最后一部分
    if current.strip():
        parts.append(current.strip())
    
    return parts


