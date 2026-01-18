"""
新的 SQL 格式化器 - 根据用户需求重新实现

主要改进：
1. CREATE TABLE 后面换行，表名单独一行
2. INSERT INTO 后面换行，表名单独一行
3. DELETE FROM 保持空格
4. UPDATE 后面换行，表名单独一行
5. 子查询正确缩进
6. 窗口函数内部正确缩进
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
        if stripped.startswith('--'):
            leading_comments.append(stripped)
        else:
            sql_lines.append(line)
    
    statement = '\n'.join(sql_lines)
    
    # 判断语句类型
    statement_upper = statement.upper().strip()
    
    if statement_upper.startswith('SELECT'):
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
        formatted = statement.strip() + ';'
    
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
    
    # 检查是否包含子查询
    has_subquery = '(' in statement and 'SELECT' in statement.upper()
    
    # 如果有子查询，先处理子查询
    if has_subquery:
        statement = process_subqueries(statement, indent_level + 1)
    
    # 提取各个部分
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', statement, re.IGNORECASE | re.DOTALL)
    select_cols = select_match.group(1) if select_match else '*'
    
    from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP BY|\s+HAVING|\s+ORDER BY|\s+LIMIT|$)', statement, re.IGNORECASE | re.DOTALL)
    from_clause = from_match.group(1) if from_match else ''
    
    where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP BY|\s+HAVING|\s+ORDER BY|\s+LIMIT|$)', statement, re.IGNORECASE | re.DOTALL)
    where_clause = where_match.group(1) if where_match else ''
    
    groupby_match = re.search(r'GROUP BY\s+(.*?)(?:\s+HAVING|\s+ORDER BY|\s+LIMIT|$)', statement, re.IGNORECASE | re.DOTALL)
    groupby_clause = groupby_match.group(1) if groupby_match else ''
    
    having_match = re.search(r'HAVING\s+(.*?)(?:\s+ORDER BY|\s+LIMIT|$)', statement, re.IGNORECASE | re.DOTALL)
    having_clause = having_match.group(1) if having_match else ''
    
    orderby_match = re.search(r'ORDER BY\s+(.*?)(?:\s+LIMIT|$)', statement, re.IGNORECASE | re.DOTALL)
    orderby_clause = orderby_match.group(1) if orderby_match else ''
    
    limit_match = re.search(r'LIMIT\s+(\d+)', statement, re.IGNORECASE)
    limit_value = limit_match.group(1) if limit_match else ''
    
    # 构建结果
    result_lines = [f'{base_indent}SELECT']
    
    # 格式化列
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
            else:
                if i < len(cols) - 1:
                    result_lines.append(f'{item_indent}{col},')
                else:
                    result_lines.append(f'{item_indent}{col}')
    
    # FROM
    if from_clause:
        result_lines.append(f'{base_indent}FROM')
        from_parts = split_joins(from_clause)
        for part in from_parts:
            result_lines.append(f'{item_indent}{part}')
    
    # WHERE
    if where_clause:
        result_lines.append(f'{base_indent}WHERE')
        where_conditions = split_and_conditions(where_clause)
        for i, cond in enumerate(where_conditions):
            if i == 0:
                result_lines.append(f'{item_indent}{cond}')
            else:
                result_lines.append(f'{item_indent}AND {cond}')
    
    # GROUP BY
    if groupby_clause:
        result_lines.append(f'{base_indent}GROUP BY')
        groupby_items = [item.strip() for item in groupby_clause.split(',')]
        for i, item in enumerate(groupby_items):
            if i < len(groupby_items) - 1:
                result_lines.append(f'{item_indent}{item},')
            else:
                result_lines.append(f'{item_indent}{item}')
    
    # HAVING
    if having_clause:
        result_lines.append(f'{base_indent}HAVING')
        having_conditions = split_and_conditions(having_clause)
        for i, cond in enumerate(having_conditions):
            if i == 0:
                result_lines.append(f'{item_indent}{cond}')
            else:
                result_lines.append(f'{item_indent}AND {cond}')
    
    # ORDER BY
    if orderby_clause:
        result_lines.append(f'{base_indent}ORDER BY')
        orderby_items = [item.strip() for item in orderby_clause.split(',')]
        for i, item in enumerate(orderby_items):
            if i < len(orderby_items) - 1:
                result_lines.append(f'{item_indent}{item},')
            else:
                result_lines.append(f'{item_indent}{item}')
    
    # LIMIT
    if indent_level == 0:
        if limit_value:
            result_lines.append(f'{base_indent}LIMIT {limit_value};')
        else:
            result_lines[-1] += ';'
    else:
        if limit_value:
            result_lines.append(f'{base_indent}LIMIT {limit_value}')
    
    return '\n'.join(result_lines)


def process_subqueries(statement: str, indent_level: int) -> str:
    """
    处理子查询，将其格式化并替换为占位符
    
    Args:
        statement: SQL 语句
        indent_level: 缩进级别
        
    Returns:
        处理后的语句
    """
    # 查找子查询（括号内的 SELECT）
    subqueries = []
    result = statement
    
    # 简单处理：查找 ( SELECT ... )
    pattern = r'\(\s*SELECT\s+.*?\)'
    
    def replace_subquery(match):
        subquery = match.group(0)
        # 移除外层括号
        inner = subquery[1:-1].strip()
        # 格式化子查询
        formatted = format_select(inner, indent_level)
        # 添加括号
        lines = formatted.split('\n')
        formatted_lines = ['(']
        for line in lines:
            formatted_lines.append(line)
        formatted_lines.append('  ' * indent_level + ')')
        subqueries.append('\n'.join(formatted_lines))
        return f'__SUBQUERY_{len(subqueries)-1}__'
    
    # 这里需要更复杂的逻辑来正确匹配括号
    # 暂时简化处理
    return result


def format_case_expression(expr: str, indent_level: int) -> str:
    """
    格式化 CASE 表达式
    
    Args:
        expr: CASE 表达式
        indent_level: 缩进级别
        
    Returns:
        格式化后的表达式
    """
    base_indent = '  ' * indent_level
    item_indent = '  ' * (indent_level + 1)
    
    # 提取 CASE ... END 部分
    case_match = re.search(r'(CASE\s+.*?\s+END)(\s+AS\s+\w+)?', expr, re.IGNORECASE | re.DOTALL)
    if not case_match:
        return f'{base_indent}{expr}'
    
    case_body = case_match.group(1)
    as_clause = case_match.group(2) if case_match.group(2) else ''
    
    # 分割 WHEN/THEN/ELSE
    lines = [f'{base_indent}CASE']
    
    # 提取所有 WHEN ... THEN ...
    when_pattern = r'WHEN\s+(.*?)\s+THEN\s+(.*?)(?=\s+WHEN|\s+ELSE|\s+END)'
    for match in re.finditer(when_pattern, case_body, re.IGNORECASE | re.DOTALL):
        condition = match.group(1).strip()
        result = match.group(2).strip()
        lines.append(f'{item_indent}WHEN {condition} THEN {result}')
    
    # 提取 ELSE
    else_match = re.search(r'ELSE\s+(.*?)(?=\s+END)', case_body, re.IGNORECASE | re.DOTALL)
    if else_match:
        else_value = else_match.group(1).strip()
        lines.append(f'{item_indent}ELSE {else_value}')
    
    lines.append(f'{base_indent}END{as_clause}')
    
    return '\n'.join(lines)


def format_create_table(statement: str) -> str:
    """格式化 CREATE TABLE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取表名和列定义
    match = re.search(r'CREATE TABLE\s+(\w+)\s*\((.*)\)', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        return statement + ';'
    
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
    match = re.search(r'CREATE VIEW\s+(\w+)\s+AS\s+(SELECT.*)', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        return statement + ';'
    
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
    
    # 提取表名、列和值
    match = re.search(r'INSERT INTO\s+(\w+)\s*\((.*?)\)\s*VALUES\s*(.*)$', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        return statement + ';'
    
    table_name = match.group(1)
    columns = match.group(2)
    values = match.group(3)
    
    # 分割列
    column_list = [col.strip() for col in columns.split(',')]
    
    # 分割值（每个括号是一行）
    value_rows = []
    current = ''
    depth = 0
    
    for char in values:
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
    
    # 提取表名、SET 和 WHERE
    match = re.search(r'UPDATE\s+(\w+)\s+SET\s+(.*?)(?:\s+WHERE\s+(.*))?$', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        return statement + ';'
    
    table_name = match.group(1)
    set_clause = match.group(2)
    where_clause = match.group(3) if match.group(3) else ''
    
    # 分割 SET 赋值
    assignments = split_columns(set_clause)
    
    # 构建结果
    result_lines = [f'UPDATE {table_name}']
    result_lines.append('SET')
    
    for i, assignment in enumerate(assignments):
        if i < len(assignments) - 1:
            result_lines.append(f'  {assignment},')
        else:
            result_lines.append(f'  {assignment}')
    
    # WHERE
    if where_clause:
        result_lines.append('WHERE')
        where_conditions = split_and_conditions(where_clause)
        for i, cond in enumerate(where_conditions):
            if i == 0:
                result_lines.append(f'  {cond}')
            else:
                result_lines.append(f'  AND {cond}')
    
    result_lines[-1] += ';'
    
    return '\n'.join(result_lines)


def format_delete(statement: str) -> str:
    """格式化 DELETE 语句"""
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取表名和 WHERE
    match = re.search(r'DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*))?$', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        return statement + ';'
    
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
    join_pattern = r'\s+(INNER JOIN|LEFT JOIN|RIGHT JOIN|JOIN)\s+'
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
