"""
新的 SQL 格式化器 - 根据用户需求重新实现

主要改进：
1. CREATE TABLE 后面换行，表名单独一行
2. INSERT INTO 后面换行，表名单独一行
3. DELETE FROM 保持空格
4. UPDATE 后面换行，表名单独一行
5. 子查询正确缩进
6. 窗口函数内部正确缩进
7. WITH 子句（CTE）正确格式化
8. CASE 语句每个 WHEN 单独一行
9. ON DUPLICATE KEY UPDATE 正确格式化
10. 修复分号重复问题
"""

import re
from typing import List, Tuple


def format_sql(text: str) -> str:
    """
    格式化 SQL 文本
    
    Args:
        text: 原始 SQL 文本
        
    Returns:
        格式化后的 SQL 文本
    """
    # 步骤1：分离头部注释和 SQL 语句
    lines = text.split('\n')
    header_lines = []
    sql_start = -1
    
    # 查找第一个 SQL 关键字
    sql_keywords = ['SELECT', 'CREATE', 'UPDATE', 'DELETE', 'INSERT', 'WITH', 'USE']
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(re.search(r'\b' + kw + r'\b', stripped, re.IGNORECASE) for kw in sql_keywords):
            sql_start = i
            break
        header_lines.append(line)
    
    if sql_start >= 0:
        sql_text = '\n'.join(lines[sql_start:])
    else:
        sql_text = text
    
    # 步骤2：按分号分割 SQL 语句
    statements = split_statements(sql_text)
    
    # 步骤3：格式化每条语句
    formatted_statements = []
    for statement in statements:
        if not statement.strip():
            continue
        formatted = format_statement(statement)
        formatted_statements.append(formatted)
    
    # 步骤4：合并结果
    result_lines = []
    for line in header_lines:
        result_lines.append(line)
    
    if result_lines:
        result_lines.append('')
    
    result_lines.append('\n\n'.join(formatted_statements))
    
    result = '\n'.join(result_lines)
    
    # 清理多余空行
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')
    
    return result.strip()


def split_statements(text: str) -> List[str]:
    """
    按分号分割 SQL 语句
    
    Args:
        text: SQL 文本
        
    Returns:
        语句列表
    """
    statements = []
    current = ''
    
    for char in text:
        current += char
        if char == ';':
            statements.append(current.strip())
            current = ''
    
    if current.strip():
        statements.append(current.strip())
    
    return statements


def format_statement(statement: str) -> str:
    """
    格式化单条 SQL 语句
    
    Args:
        statement: SQL 语句
        
    Returns:
        格式化后的语句
    """
    # 分离前导注释
    lines = statement.split('\n')
    leading_comments = []
    sql_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('--') or stripped.startswith('/*'):
            leading_comments.append(stripped)
        else:
            sql_lines.append(line)
    
    statement = '\n'.join(sql_lines)
    
    # 判断语句类型
    statement_upper = statement.upper().strip()
    
    # 检查是否是 CREATE TABLE ... AS WITH ... 或 CREATE TEMPORARY TABLE ... AS WITH ...
    if re.search(r'CREATE\s+(TEMPORARY\s+)?TABLE.*\s+AS\s+WITH\s+', statement_upper):
        formatted = format_create_table_as_with(statement)
    elif statement_upper.startswith('WITH'):
        # 独立的 WITH 语句
        formatted = format_with_clause(statement)
    elif statement_upper.startswith('SELECT'):
        formatted = format_select(statement)
    elif statement_upper.startswith('CREATE TABLE'):
        formatted = format_create_table(statement)
    elif statement_upper.startswith('CREATE VIEW'):
        formatted = format_create_view(statement)
    elif statement_upper.startswith('CREATE INDEX'):
        formatted = format_create_index(statement)
    elif statement_upper.startswith('CREATE DATABASE'):
        formatted = format_create_database(statement)
    elif statement_upper.startswith('INSERT'):
        formatted = format_insert(statement)
    elif statement_upper.startswith('UPDATE'):
        formatted = format_update(statement)
    elif statement_upper.startswith('DELETE'):
        formatted = format_delete(statement)
    elif statement_upper.startswith('USE'):
        formatted = format_use(statement)
    else:
        # 确保以分号结尾（如果原本没有）
        formatted = statement.strip()
        if not formatted.endswith(';'):
            formatted += ';'
    
    # 合并前导注释
    if leading_comments:
        formatted = '\n'.join(leading_comments) + '\n' + formatted
    
    return formatted



def format_select(statement: str, indent_level: int = 0) -> str:
    """
    格式化 SELECT 语句
    
    Args:
        statement: SELECT 语句
        indent_level: 缩进级别（用于子查询）
        
    Returns:
        格式化后的语句
    """
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 基础缩进
    base_indent = '  ' * indent_level
    item_indent = '  ' * (indent_level + 1)
    
    # 使用新的解析方法提取各个部分
    parts = parse_select_statement(statement)
    
    # 构建结果
    result_lines = [f'{base_indent}SELECT']
    
    # 格式化列
    select_cols = parts.get('select', '*')
    if select_cols.strip() == '*':
        result_lines.append(f'{item_indent}*')
    else:
        cols = split_columns(select_cols)
        for i, col in enumerate(cols):
            # 处理 CASE 语句
            if 'CASE' in col.upper():
                formatted_case = format_case_expression(col, indent_level + 1)
                if i < len(cols) - 1:
                    result_lines.append(formatted_case.rstrip() + ',')
                else:
                    result_lines.append(formatted_case)
            # 处理子查询
            elif '(' in col and 'SELECT' in col.upper():
                formatted_subquery = format_subquery_in_column(col, indent_level + 1)
                if i < len(cols) - 1:
                    result_lines.append(formatted_subquery.rstrip() + ',')
                else:
                    result_lines.append(formatted_subquery)
            else:
                if i < len(cols) - 1:
                    result_lines.append(f'{item_indent}{col},')
                else:
                    result_lines.append(f'{item_indent}{col}')
    
    # FROM
    from_clause = parts.get('from', '')
    if from_clause:
        result_lines.append(f'{base_indent}FROM')
        from_parts = split_joins(from_clause)
        for part in from_parts:
            result_lines.append(f'{item_indent}{part}')
    
    # WHERE
    where_clause = parts.get('where', '')
    if where_clause:
        result_lines.append(f'{base_indent}WHERE')
        where_conditions = split_and_conditions(where_clause)
        for i, cond in enumerate(where_conditions):
            # 处理子查询
            if '(' in cond and 'SELECT' in cond.upper():
                formatted_cond = format_condition_with_subquery(cond, indent_level + 1)
                if i == 0:
                    result_lines.append(f'{item_indent}{formatted_cond}')
                else:
                    result_lines.append(f'{item_indent}AND {formatted_cond}')
            else:
                if i == 0:
                    result_lines.append(f'{item_indent}{cond}')
                else:
                    result_lines.append(f'{item_indent}AND {cond}')
    
    # GROUP BY
    groupby_clause = parts.get('group_by', '')
    if groupby_clause:
        result_lines.append(f'{base_indent}GROUP BY')
        groupby_items = [item.strip() for item in groupby_clause.split(',')]
        for i, item in enumerate(groupby_items):
            if i < len(groupby_items) - 1:
                result_lines.append(f'{item_indent}{item},')
            else:
                result_lines.append(f'{item_indent}{item}')
    
    # HAVING
    having_clause = parts.get('having', '')
    if having_clause:
        result_lines.append(f'{base_indent}HAVING')
        having_conditions = split_and_conditions(having_clause)
        for i, cond in enumerate(having_conditions):
            if i == 0:
                result_lines.append(f'{item_indent}{cond}')
            else:
                result_lines.append(f'{item_indent}AND {cond}')
    
    # ORDER BY
    orderby_clause = parts.get('order_by', '')
    if orderby_clause:
        result_lines.append(f'{base_indent}ORDER BY')
        orderby_items = [item.strip() for item in orderby_clause.split(',')]
        for i, item in enumerate(orderby_items):
            if i < len(orderby_items) - 1:
                result_lines.append(f'{item_indent}{item},')
            else:
                result_lines.append(f'{item_indent}{item}')
    
    # LIMIT
    limit_value = parts.get('limit', '')
    if indent_level == 0:
        if limit_value:
            result_lines.append(f'{base_indent}LIMIT {limit_value};')
        else:
            # 只在顶层 SELECT 添加分号
            if not result_lines[-1].endswith(';'):
                result_lines[-1] += ';'
    else:
        if limit_value:
            result_lines.append(f'{base_indent}LIMIT {limit_value}')
    
    return '\n'.join(result_lines)


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
            # 检查是否是关键字的开始
            remaining = statement[i:].upper()
            
            if remaining.startswith('FROM '):
                parts[current_part] = current_content.strip()
                current_part = 'from'
                current_content = ''
                i += 5  # len('FROM ')
                continue
            elif remaining.startswith('WHERE '):
                parts[current_part] = current_content.strip()
                current_part = 'where'
                current_content = ''
                i += 6  # len('WHERE ')
                continue
            elif remaining.startswith('GROUP BY '):
                parts[current_part] = current_content.strip()
                current_part = 'group_by'
                current_content = ''
                i += 9  # len('GROUP BY ')
                continue
            elif remaining.startswith('HAVING '):
                parts[current_part] = current_content.strip()
                current_part = 'having'
                current_content = ''
                i += 7  # len('HAVING ')
                continue
            elif remaining.startswith('ORDER BY '):
                parts[current_part] = current_content.strip()
                current_part = 'order_by'
                current_content = ''
                i += 9  # len('ORDER BY ')
                continue
            elif remaining.startswith('LIMIT '):
                parts[current_part] = current_content.strip()
                current_part = 'limit'
                current_content = ''
                i += 6  # len('LIMIT ')
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


def format_subquery_in_column(col: str, indent_level: int) -> str:
    """格式化列中的子查询"""
    # 提取子查询
    match = re.search(r'\((SELECT.+?)\)', col, re.IGNORECASE | re.DOTALL)
    if not match:
        return '  ' * indent_level + col
    
    subquery = match.group(1)
    formatted_subquery = format_select(subquery, indent_level + 1)
    
    # 替换原始子查询
    result = col.replace(match.group(0), f'(\n{formatted_subquery}\n' + '  ' * indent_level + ')')
    
    return '  ' * indent_level + result


def format_condition_with_subquery(cond: str, indent_level: int) -> str:
    """格式化包含子查询的条件"""
    # 查找 IN (SELECT ...) 或其他包含子查询的模式
    match = re.search(r'IN\s*\((SELECT.+?)\)', cond, re.IGNORECASE | re.DOTALL)
    if not match:
        return cond
    
    subquery = match.group(1)
    formatted_subquery = format_select(subquery, indent_level + 1)
    
    # 替换原始子查询
    result = cond.replace(match.group(0), f'IN(\n{formatted_subquery}\n' + '  ' * indent_level + ')')
    
    return result


def format_case_expression(expr: str, indent_level: int) -> str:
    """
    格式化 CASE 表达式
    
    Args:
        expr: CASE 表达式（可能包含赋值，如 "user_level = CASE ... END"）
        indent_level: 缩进级别
        
    Returns:
        格式化后的表达式
    """
    base_indent = '  ' * indent_level
    item_indent = '  ' * (indent_level + 1)
    
    # 检查是否有赋值（如 "user_level = CASE ..."）
    assignment_prefix = ''
    case_start = expr.upper().find('CASE')
    if case_start > 0:
        assignment_prefix = expr[:case_start].strip() + ' '
        expr = expr[case_start:]
    
    # 提取 CASE ... END 部分
    case_match = re.search(r'(CASE\s+.*?\s+END)(\s+AS\s+\w+)?', expr, re.IGNORECASE | re.DOTALL)
    if not case_match:
        return f'{base_indent}{assignment_prefix}{expr}'
    
    case_body = case_match.group(1)
    as_clause = case_match.group(2) if case_match.group(2) else ''
    
    # 分割 WHEN/THEN/ELSE - 使用深度感知的解析
    lines = [f'{base_indent}{assignment_prefix}CASE']
    
    # 手动解析 WHEN/THEN，考虑括号深度
    i = 4  # 跳过 'CASE'
    while i < len(case_body):
        # 跳过空白
        while i < len(case_body) and case_body[i].isspace():
            i += 1
        
        if i >= len(case_body):
            break
        
        # 检查 WHEN
        if case_body[i:i+4].upper() == 'WHEN':
            i += 4
            # 跳过空白
            while i < len(case_body) and case_body[i].isspace():
                i += 1
            
            # 提取条件（直到 THEN，考虑括号）
            condition = ''
            depth = 0
            while i < len(case_body):
                if case_body[i] == '(':
                    depth += 1
                    condition += case_body[i]
                elif case_body[i] == ')':
                    depth -= 1
                    condition += case_body[i]
                elif depth == 0 and case_body[i:i+4].upper() == 'THEN':
                    break
                else:
                    condition += case_body[i]
                i += 1
            
            # 跳过 THEN
            if case_body[i:i+4].upper() == 'THEN':
                i += 4
            
            # 跳过空白
            while i < len(case_body) and case_body[i].isspace():
                i += 1
            
            # 提取结果（直到下一个 WHEN、ELSE 或 END，考虑括号）
            result = ''
            depth = 0
            while i < len(case_body):
                if case_body[i] == '(':
                    depth += 1
                    result += case_body[i]
                elif case_body[i] == ')':
                    depth -= 1
                    result += case_body[i]
                elif depth == 0:
                    next_keyword = case_body[i:i+4].upper()
                    if next_keyword == 'WHEN' or next_keyword == 'ELSE' or next_keyword.startswith('END'):
                        break
                    result += case_body[i]
                else:
                    result += case_body[i]
                i += 1
            
            # 格式化条件中的子查询
            condition = condition.strip()
            if '(' in condition and 'SELECT' in condition.upper():
                # 找到 IN( 或其他操作符后的子查询
                in_match = re.search(r'(.*?IN\s*)\((SELECT.+)\)$', condition, re.IGNORECASE | re.DOTALL)
                if in_match:
                    prefix = in_match.group(1)
                    subquery = in_match.group(2)
                    formatted_subquery = format_select(subquery, indent_level + 2)
                    condition = f'{prefix}(\n{formatted_subquery}\n{item_indent})'
            
            lines.append(f'{item_indent}WHEN {condition} THEN {result.strip()}')
        
        # 检查 ELSE
        elif case_body[i:i+4].upper() == 'ELSE':
            i += 4
            # 跳过空白
            while i < len(case_body) and case_body[i].isspace():
                i += 1
            
            # 提取 ELSE 值（直到 END）
            else_value = ''
            depth = 0
            while i < len(case_body):
                if case_body[i] == '(':
                    depth += 1
                    else_value += case_body[i]
                elif case_body[i] == ')':
                    depth -= 1
                    else_value += case_body[i]
                elif depth == 0 and case_body[i:i+3].upper() == 'END':
                    break
                else:
                    else_value += case_body[i]
                i += 1
            
            lines.append(f'{item_indent}ELSE {else_value.strip()}')
        
        # 检查 END
        elif case_body[i:i+3].upper() == 'END':
            break
        else:
            i += 1
    
    lines.append(f'{base_indent}END{as_clause}')
    
    return '\n'.join(lines)



def format_create_table_as_with(statement: str) -> str:
    """格式化 CREATE TABLE ... AS WITH ... 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取 CREATE TABLE 部分和 WITH 部分
    # 匹配 CREATE [TEMPORARY] TABLE [IF NOT EXISTS] table_name AS WITH ...
    match = re.search(
        r'(CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\w.]+)\s+AS\s+(WITH\s+.+)',
        statement,
        re.IGNORECASE | re.DOTALL
    )
    
    if not match:
        # 如果不匹配，回退到普通 CREATE TABLE
        return format_create_table(statement)
    
    create_part = match.group(1)
    with_part = match.group(2)
    
    # 格式化 WITH 子句
    formatted_with = format_with_clause(with_part)
    
    # 构建结果
    result = f'{create_part} AS\n{formatted_with}'
    
    return result


def format_with_clause(statement: str) -> str:
    """
    格式化 WITH 子句（CTE - Common Table Expression）
    
    Args:
        statement: WITH 子句
        
    Returns:
        格式化后的 WITH 子句
    """
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取 WITH 关键字后的内容
    match = re.search(r'WITH\s+(.+)', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        return statement
    
    content = match.group(1)
    
    # 使用更简单的方法：找到所有 CTE_NAME AS (...)
    ctes = []
    final_select = None
    
    i = 0
    while i < len(content):
        # 跳过空白
        while i < len(content) and content[i].isspace():
            i += 1
        
        if i >= len(content):
            break
        
        # 查找 CTE 名称
        cte_name_match = re.match(r'(\w+)\s+AS\s*\(', content[i:], re.IGNORECASE)
        if not cte_name_match:
            # 可能是最终的 SELECT
            if content[i:].strip().upper().startswith('SELECT'):
                final_select = content[i:].strip()
            break
        
        cte_name = cte_name_match.group(1)
        i += cte_name_match.end()
        
        # 找到匹配的右括号
        depth = 1
        start = i
        while i < len(content) and depth > 0:
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
            i += 1
        
        # 提取 CTE 内容（不包括外层括号）
        cte_content = content[start:i-1].strip()
        ctes.append((cte_name, cte_content))
        
        # 跳过逗号
        while i < len(content) and (content[i].isspace() or content[i] == ','):
            i += 1
    
    # 格式化所有 CTE
    result_lines = ['WITH']
    
    for idx, (cte_name, cte_content) in enumerate(ctes):
        # 格式化 SELECT 语句（缩进级别为 1）
        formatted_select = format_select(cte_content, indent_level=1)
        
        if idx == 0:
            result_lines.append(f'{cte_name} AS (')
        else:
            result_lines.append(',')
            result_lines.append(f'{cte_name} AS (')
        
        # 添加格式化的 SELECT（已经有缩进）
        result_lines.append(formatted_select)
        result_lines.append(')')
    
    # 添加最终的 SELECT
    if final_select:
        formatted_final_select = format_select(final_select, indent_level=0)
        result_lines.append(formatted_final_select)
    
    return '\n'.join(result_lines)


def format_create_table(statement: str) -> str:
    """格式化 CREATE TABLE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取表名和列定义
    match = re.search(r'CREATE\s+TABLE\s+(\w+)\s*\((.*)\)', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    table_name = match.group(1)
    columns_def = match.group(2)
    
    # 分割列定义
    columns = split_columns(columns_def)
    
    # 构建结果 - CREATE TABLE 后换行，表名单独一行，列定义缩进2个空格
    result_lines = ['CREATE TABLE']
    result_lines.append(f'{table_name} (')
    
    for i, col in enumerate(columns):
        if i < len(columns) - 1:
            result_lines.append(f'  {col},')
        else:
            result_lines.append(f'  {col}')
    
    result_lines.append(');')
    
    return '\n'.join(result_lines)


def format_create_view(statement: str) -> str:
    """格式化 CREATE VIEW 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取视图名和 SELECT 语句
    match = re.search(r'CREATE\s+VIEW\s+(\w+)\s+AS\s+(SELECT.*)', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    view_name = match.group(1)
    select_statement = match.group(2)
    
    # 格式化 SELECT 语句
    formatted_select = format_select(select_statement)
    
    # 构建结果
    result = f'CREATE VIEW {view_name} AS\n{formatted_select}'
    
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



def format_insert(statement: str) -> str:
    """格式化 INSERT 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 检查是否有 ON DUPLICATE KEY UPDATE
    on_duplicate_match = re.search(
        r'(.*?)\s+ON\s+DUPLICATE\s+KEY\s+UPDATE\s+(.+)',
        statement,
        re.IGNORECASE | re.DOTALL
    )
    
    if on_duplicate_match:
        # 有 ON DUPLICATE KEY UPDATE
        insert_part = on_duplicate_match.group(1).strip()
        update_part = on_duplicate_match.group(2).strip()
        
        # 格式化 INSERT 部分
        formatted_insert = format_insert_basic(insert_part)
        
        # 移除 INSERT 部分末尾的分号（如果有）
        if formatted_insert.endswith(';'):
            formatted_insert = formatted_insert[:-1]
        
        # 格式化 UPDATE 部分
        update_assignments = split_columns(update_part)
        
        result_lines = formatted_insert.split('\n')
        result_lines.append('ON DUPLICATE KEY')
        result_lines.append('UPDATE')
        
        for i, assignment in enumerate(update_assignments):
            if i < len(update_assignments) - 1:
                result_lines.append(f'  {assignment},')
            else:
                result_lines.append(f'  {assignment};')
        
        return '\n'.join(result_lines)
    else:
        # 没有 ON DUPLICATE KEY UPDATE，使用基本格式化
        return format_insert_basic(statement)


def format_insert_basic(statement: str) -> str:
    """格式化基本 INSERT 语句（不包含 ON DUPLICATE KEY UPDATE）"""
    # 先检查是否是 INSERT INTO ... SELECT
    select_match = re.search(r'INSERT\s+INTO\s+(\w+)\s*\((.*?)\)\s*SELECT\s+(.+)', statement, re.IGNORECASE | re.DOTALL)
    if select_match:
        table_name = select_match.group(1)
        columns = select_match.group(2)
        select_part = 'SELECT ' + select_match.group(3)
        
        # 格式化 SELECT 语句
        formatted_select = format_select(select_part, indent_level=0)
        result = f'INSERT INTO {table_name} ({columns})\n{formatted_select}'
        return result
    
    # 提取表名、列和值
    match = re.search(r'INSERT\s+INTO\s+(\w+)\s*\((.*?)\)\s*VALUES\s+(.+)', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    table_name = match.group(1)
    columns = match.group(2)
    values_or_select = match.group(3)
    
    # 分割列
    column_list = [col.strip() for col in columns.split(',')]
    
    # 分割值（每个括号是一行）
    value_rows = []
    current = ''
    depth = 0
    
    for char in values_or_select:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            current += char
            if depth == 0:
                value_rows.append(current.strip())
                current = ''
                continue
        elif char == ',' and depth == 0:
            continue
        current += char
    
    # 构建结果 - INSERT INTO 表名和列在同一行，VALUES 换行，每行值缩进2个空格
    result_lines = [f'INSERT INTO {table_name} ({columns})']
    result_lines.append('VALUES')
    
    for i, row in enumerate(value_rows):
        if i < len(value_rows) - 1:
            result_lines.append(f'  {row},')
        else:
            result_lines.append(f'  {row};')
    
    return '\n'.join(result_lines)


def format_update(statement: str) -> str:
    """格式化 UPDATE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 使用深度感知的解析
    parts = parse_update_statement(statement)
    
    if not parts['table']:
        # 解析失败，确保以分号结尾
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    table_name = parts['table']
    set_clause = parts['set']
    where_clause = parts['where']
    
    # 分割 SET 赋值
    assignments = split_columns(set_clause)
    
    # 构建结果
    result_lines = [f'UPDATE {table_name}']
    result_lines.append('SET')
    
    for i, assignment in enumerate(assignments):
        # 处理 CASE 语句
        if 'CASE' in assignment.upper():
            formatted_case = format_case_expression(assignment, indent_level=1)
            if i < len(assignments) - 1:
                result_lines.append(formatted_case.rstrip() + ',')
            else:
                result_lines.append(formatted_case)
        else:
            if i < len(assignments) - 1:
                result_lines.append(f'  {assignment},')
            else:
                result_lines.append(f'  {assignment}')
    
    # WHERE
    if where_clause:
        result_lines.append('WHERE')
        where_conditions = split_and_conditions(where_clause)
        for i, cond in enumerate(where_conditions):
            # 处理子查询
            if '(' in cond and 'SELECT' in cond.upper():
                formatted_cond = format_condition_with_subquery(cond, indent_level=1)
                if i == 0:
                    result_lines.append(f'  {formatted_cond}')
                else:
                    result_lines.append(f'  AND {formatted_cond}')
            else:
                if i == 0:
                    result_lines.append(f'  {cond}')
                else:
                    result_lines.append(f'  AND {cond}')
    
    # 添加分号
    result_lines[-1] += ';'
    
    return '\n'.join(result_lines)


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


def format_delete(statement: str) -> str:
    """格式化 DELETE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取表名和 WHERE
    match = re.search(r'DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*))?$', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    table_name = match.group(1)
    where_clause = match.group(2) if match.group(2) else ''
    
    # 构建结果
    result_lines = [f'DELETE FROM {table_name}']
    
    # WHERE
    if where_clause:
        result_lines.append('WHERE')
        where_conditions = split_and_conditions(where_clause)
        for i, cond in enumerate(where_conditions):
            if i == 0:
                result_lines.append(f'  {cond}')
            else:
                result_lines.append(f'  AND {cond}')
    
    # 添加分号
    result_lines[-1] += ';'
    
    return '\n'.join(result_lines)


def format_use(statement: str) -> str:
    """格式化 USE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 确保以分号结尾
    if not statement.endswith(';'):
        statement += ';'
    
    return statement



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


def split_joins(text: str) -> List[str]:
    """
    分割 JOIN 子句
    
    Args:
        text: FROM 子句文本
        
    Returns:
        JOIN 部分列表
    """
    parts = []
    
    # 分割 JOIN
    join_pattern = r'\s+(INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|JOIN)\s+'
    segments = re.split(join_pattern, text, flags=re.IGNORECASE)
    
    if segments:
        parts.append(segments[0].strip())
    
    i = 1
    while i < len(segments):
        if i + 1 < len(segments):
            join_type = segments[i]
            join_clause = segments[i + 1].strip()
            parts.append(f'{join_type} {join_clause}')
            i += 2
        else:
            i += 1
    
    return parts


def split_and_conditions(text: str) -> List[str]:
    """
    分割 AND 条件（考虑括号内的 AND）
    
    Args:
        text: WHERE 或 HAVING 子句文本
        
    Returns:
        条件列表
    """
    conditions = []
    current = ''
    depth = 0
    
    i = 0
    while i < len(text):
        char = text[i]
        
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif depth == 0 and text[i:i+5].upper() == ' AND ':
            cond = current.strip()
            if cond:
                conditions.append(cond)
            current = ''
            i += 5
            continue
        
        current += char
        i += 1
    
    if current.strip():
        conditions.append(current.strip())
    
    return conditions


if __name__ == '__main__':
    # 测试
    test_sql = """-- 测试
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(50)
);

INSERT INTO employees (id, name) VALUES (1, 'John'), (2, 'Jane');

SELECT * FROM employees WHERE id = 1;

UPDATE employees SET name = 'John Doe' WHERE id = 1;

DELETE FROM employees WHERE id = 1;
"""
    
    print(format_sql(test_sql))
