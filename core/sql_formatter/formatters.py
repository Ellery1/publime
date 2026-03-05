"""
SQL格式化器主格式化模块

包含format_sql、format_statement、format_select、format_insert、format_update、format_delete等主要格式化函数
"""

import re
from typing import List

from .parser import (
    split_statements,
    parse_select_statement,
    parse_update_statement,
    split_columns,
    split_and_conditions,
    split_union_all
)
from .utils import (
    separate_keywords,
    add_space_after_comma,
    add_space_around_equals,
    format_in_clause,
    remove_space_before_paren,
    extract_inline_comment,
    compress_sql_preserving_comments
)
from .expression_formatters import (
    format_case_expression,
    format_json_object,
    format_from_clause,
    format_with_clause,
    format_create_table_as_with,
    format_window_function
)
from .ddl_formatters import (
    format_create_table,
    format_create_view,
    format_create_index,
    format_create_database,
    format_use
)


def format_sql(text: str) -> str:
    """
    格式化 SQL 文本
    
    Args:
        text: 原始 SQL 文本
        
    Returns:
        格式化后的 SQL 文本,如果格式化失败则返回原始文本
    """
    try:
        # 步骤0：在逗号后添加空格
        text = add_space_after_comma(text)
        
        # 步骤1：分离头部注释和 SQL 语句
        lines = text.split('\n')
        header_lines = []
        sql_start = -1
        
        # print(f"[DEBUG] 总行数: {len(lines)}")
        
        # 查找第一个 SQL 关键字
        sql_keywords = ['SELECT', 'CREATE', 'UPDATE', 'DELETE', 'INSERT', 'WITH', 'USE']
        for i, line in enumerate(lines):
            stripped = line.strip()
            # print(f"[DEBUG] 行 {i+1}: '{stripped}'")
            if any(stripped.upper().startswith(kw) for kw in sql_keywords):
                sql_start = i
                # print(f"[DEBUG] 找到SQL关键字开头的行: {i+1}")
                break
            if any(kw in stripped.upper() for kw in sql_keywords):
                sql_start = i
                # print(f"[DEBUG] 找到包含SQL关键字的行: {i+1}")
                break
            header_lines.append(line)
        
        # print(f"[DEBUG] sql_start: {sql_start}")
        # print(f"[DEBUG] 头部注释行数: {len(header_lines)}")
        # print(f"[DEBUG] 头部注释内容: {header_lines}")
        
        if sql_start >= 0:
            sql_text = '\n'.join(lines[sql_start:])
        else:
            sql_text = text
        
        # 移除header_lines中的所有空行
        header_lines = [line for line in header_lines if line.strip()]
        # print(f"[DEBUG] 移除空行后的头部注释内容: {header_lines}")
        
        # 步骤2：按分号分割 SQL 语句
        statements = split_statements(sql_text)
        
        # 步骤3：格式化每条语句
        formatted_statements = []
        for idx, statement in enumerate(statements):
            if not statement.strip():
                continue
            # 跳过纯注释语句
            if all(line.strip().startswith('--') or line.strip() == '' for line in statement.split('\n')):
                continue
            formatted = format_statement(statement)
            formatted_statements.append(formatted)
        
        # 步骤4：合并结果
        result_lines = []
        for line in header_lines:
            # 保持头部注释的原始格式，不添加额外缩进
            result_lines.append(line)
        
        # 检查原始文本中语句之间的空行模式
        # 简单策略：在原始文本中查找连续的两个分号之间是否有空行
        original_has_blank_lines = '\n\n' in sql_text or '\n;\n\n' in sql_text
        
        # 如果原始文本中有空行模式，在格式化语句之间添加空行
        if original_has_blank_lines:
            for i, formatted in enumerate(formatted_statements):
                result_lines.append(formatted)
                # 在语句之间添加空行（除了最后一个）
                if i < len(formatted_statements) - 1:
                    result_lines.append('')
        else:
            # 没有空行模式，直接连接
            for formatted in formatted_statements:
                result_lines.append(formatted)
        
        result = '\n'.join(result_lines)
        
        # 清理多余空行
        while '\n\n\n' in result:
            result = result.replace('\n\n\n', '\n\n')
        
        result = result.strip()
        
        return result
    except Exception as e:
        # 格式化失败,返回原始文本
        print(f"[ERROR] SQL formatting error: {e}")
        import traceback
        traceback.print_exc()
        return text


def format_statement(statement: str) -> str:
    """
    格式化单条 SQL 语句
    
    Args:
        statement: SQL 语句
        
    Returns:
        格式化后的语句
    """
    # 提取前导注释
    stmt_lines = statement.split('\n')
    leading_comments = []
    sql_start_idx = -1
    in_multiline_comment = False
    multiline_comment_start_idx = -1
    
    for i, line in enumerate(stmt_lines):
        stripped = line.strip()
        
        if not in_multiline_comment:
            # 检查是否开始多行注释
            if stripped.startswith('/*'):
                in_multiline_comment = True
                multiline_comment_start_idx = i
                leading_comments.append(line)
                # 如果这行同时包含结束标记，直接结束
                if '*/' in stripped:
                    in_multiline_comment = False
            # 检查是否是单行注释
            elif stripped.startswith('--'):
                leading_comments.append(line)
            else:
                # 找到第一个非注释行
                sql_start_idx = i
                break
        else:
            # 处于多行注释中
            leading_comments.append(line)
            # 检查是否结束多行注释
            if '*/' in stripped:
                in_multiline_comment = False
    
    # 如果到达文件末尾仍在多行注释中，继续处理
    if in_multiline_comment and sql_start_idx == -1:
        sql_start_idx = len(stmt_lines)
    
    # 重新组合SQL（不包含前导注释）
    if sql_start_idx >= 0:
        sql_without_comments = '\n'.join(stmt_lines[sql_start_idx:])
    else:
        # 全是注释，直接返回
        return statement
    
    # 记录原始SQL是否有分号
    original_has_semicolon = sql_without_comments.strip().endswith(';')
    
    # 确保SQL语句以分号结尾（用于解析）
    if not sql_without_comments.strip().endswith(';'):
        sql_without_comments = sql_without_comments.strip() + ';'
    
    # 新步骤：在合并成一行之前，先提取并标记行内注释
    # 使用 __COMMENT__ 标记来保护注释
    comment_pattern = r'(--[^\n]*)'
    comment_matches = list(re.finditer(comment_pattern, sql_without_comments))
    
    # 替换注释为标记
    sql_with_markers = sql_without_comments
    for match in reversed(comment_matches):  # 从后往前替换，避免位置偏移
        comment_text = match.group(1)
        sql_with_markers = sql_with_markers[:match.start()] + f'__COMMENT__{comment_text}__COMMENT__' + sql_with_markers[match.end():]
    
    # 清理SQL语句，移除多余的空白字符（但保留注释标记）
    sql_with_markers = ' '.join(sql_with_markers.split())
    
    # 新步骤：分离关键字，解决如country_rankFROM这样的问题
    sql_with_markers = separate_keywords(sql_with_markers)
    
    # 恢复注释
    sql_without_comments = re.sub(r'__COMMENT__(--.*?)__COMMENT__', r'\n\1\n', sql_with_markers)
    
    # 如果原始SQL没有分号，移除我们添加的分号
    if not original_has_semicolon:
        sql_without_comments = sql_without_comments.rstrip(';').strip()
    
    # 判断语句类型
    statement_upper = sql_without_comments.upper().strip()
    
    # 检查是否包含UNION ALL - 不要求word boundary，因为可能是1union allselect这样的格式
    if 'UNION' in statement_upper and 'ALL' in statement_upper:
        formatted = format_union_query(sql_without_comments)
    # 检查是否是 CREATE TABLE ... AS WITH ... 或 CREATE TEMPORARY TABLE ... AS WITH ...
    elif re.search(r'CREATE\s+(TEMPORARY\s+)?TABLE.*\s+AS\s+WITH\s+', statement_upper):
        formatted = format_create_table_as_with(sql_without_comments)
    elif statement_upper.startswith('WITH'):
        # 独立的 WITH 语句
        formatted = format_with_clause(sql_without_comments)
    elif statement_upper.startswith('SELECT'):
        formatted = format_select(sql_without_comments)
    elif statement_upper.startswith('CREATE TABLE'):
        formatted = format_create_table(sql_without_comments)
    elif statement_upper.startswith('CREATE VIEW'):
        formatted = format_create_view(sql_without_comments)
    elif statement_upper.startswith('CREATE INDEX'):
        formatted = format_create_index(sql_without_comments)
    elif statement_upper.startswith('CREATE DATABASE'):
        formatted = format_create_database(sql_without_comments)
    elif statement_upper.startswith('INSERT'):
        formatted = format_insert(sql_without_comments)
    elif statement_upper.startswith('UPDATE'):
        formatted = format_update(sql_without_comments)
    elif statement_upper.startswith('DELETE'):
        formatted = format_delete(sql_without_comments)
    elif statement_upper.startswith('USE'):
        formatted = format_use(sql_without_comments)
    else:
        # 确保以分号结尾（如果原本没有）
        formatted = sql_without_comments.strip()
        if not formatted.endswith(';'):
            formatted += ';'
    
    # 将前导注释添加回去（保持原始格式，不添加额外缩进）
    if leading_comments:
        # 保持前导注释的原始格式，不添加额外缩进
        result_lines = leading_comments + [formatted]
        return '\n'.join(result_lines)
    else:
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
    # 步骤0: 提取行内注释（在SQL语句中间的注释）
    # 策略：找到注释，并确定它在哪一列之后
    lines = statement.split('\n')
    inline_comments_by_col = {}  # {列索引: 注释内容}
    
    # 先将所有行合并，但保留注释的位置标记
    merged_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('--'):
            # 单行注释，用特殊标记替换
            merged_lines.append(f'__COMMENT__{stripped}__COMMENT__')
        else:
            merged_lines.append(line)
    
    statement_with_markers = '\n'.join(merged_lines)
    
    # 步骤1: 在主要SQL关键字前后添加空格，但不在括号内添加
    # 添加空格在关键字前后，但只在括号外
    # 同时将关键字转换为大写（除了AS，保留原始大小写）
    keywords_patterns = [
        (r'(?i)(?![^(]*\))\b(select)\b', lambda m: m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(from)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(where)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(and)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(or)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(group\s+by)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(order\s+by)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(join)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(on)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(left)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(right)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(inner)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(outer)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(as)\b', lambda m: ' ' + m.group(1) + ' '),  # 保留AS的原始大小写
        (r'(?i)(?![^(]*\))\b(limit)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(offset)\b', lambda m: ' ' + m.group(1).upper() + ' '),
        (r'(?i)(?![^(]*\))\b(asc)\b', lambda m: ' ' + m.group(1).upper()),
        (r'(?i)(?![^(]*\))\b(desc)\b', lambda m: ' ' + m.group(1).upper())
    ]
    
    for pattern, replacement in keywords_patterns:
        statement_with_markers = re.sub(pattern, replacement, statement_with_markers)
    
    # 清理多余空格（但保留注释标记）
    statement_with_markers = ' '.join(statement_with_markers.split())
    
    # 记录原始SQL是否有分号
    has_semicolon = statement_with_markers.rstrip().endswith(';')
    
    # 移除分号
    statement_with_markers = statement_with_markers.rstrip(';').strip()
    
    # 使用新的解析方法提取各个部分
    parts = parse_select_statement(statement_with_markers)
    
    # 定义注释模式
    comment_pattern = r'__COMMENT__(--.*?)__COMMENT__'
    
    # 从所有部分中恢复注释（移除标记，但保留注释内容）
    for key in parts:
        if parts[key]:
            # 将 __COMMENT__--注释__COMMENT__ 替换为 \n--注释\n
            parts[key] = re.sub(comment_pattern, r'\n\1\n', parts[key])
    
    # 从SELECT部分提取注释（用于确定注释位置）
    select_cols_with_markers = parts.get('select', '*')
    
    # 提取注释并确定它们的位置（在移除标记之前）
    # 注意：这里我们需要使用原始的带标记的版本
    select_cols_original = parse_select_statement(statement_with_markers).get('select', '*')
    comments_found = list(re.finditer(comment_pattern, select_cols_original))
    
    # 确定每个注释在哪一列之后
    for comment_match in comments_found:
        comment_text = comment_match.group(1)
        comment_pos = comment_match.start()
        
        # 计算注释前有多少个逗号（在深度为0时）
        col_index = 0
        depth = 0
        for i in range(comment_pos):
            char = select_cols_with_markers[i]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                col_index += 1
        
        inline_comments_by_col[col_index] = comment_text
    
    # 获取纯净的 SELECT 列（已经移除了注释标记）
    select_cols = parts.get('select', '*')
    
    # 移除 select_cols 中的注释，因为这些注释已经在 inline_comments_by_col 中处理过了
    # 分割成行
    select_lines = select_cols.split('\n')
    cleaned_select_cols = []
    for line in select_lines:
        line = line.strip()
        if not line:
            continue
        # 跳过注释行
        if line.startswith('--'):
            continue
        cleaned_select_cols.append(line)
    # 重新组合成一行，保留原有的逗号
    select_cols = ' '.join(cleaned_select_cols)
    # 修复可能出现的双逗号问题（注释被移除后）
    select_cols = re.sub(r',\s*,', ',', select_cols)
    
    # 计算基础缩进（用于子查询）
    base_indent = '  ' * indent_level
    
    # 构建结果 - 使用大写关键字
    result_lines = [base_indent + 'SELECT']
    
    # 格式化列 - 每列单独一行,缩进2个空格
    if select_cols.strip() == '*':
        result_lines.append(base_indent + '  *')
    else:
        # 分割列
        cols = split_columns(select_cols)
        for i, col in enumerate(cols):
            # 检查是否有注释在这一列之前
            if i in inline_comments_by_col:
                result_lines.append(base_indent + '  ' + inline_comments_by_col[i])
            
            # 检查列中是否包含多行注释
            if '/*' in col:
                # 提取并处理多行注释
                lines = col.split('\n')
                comment_lines = []
                sql_lines = []
                
                in_multiline_comment = False
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if '/*' in line and '*/' in line:
                        # 单行多行注释
                        comment_lines.append(line)
                    elif '/*' in line:
                        # 开始多行注释
                        in_multiline_comment = True
                        comment_lines.append(line)
                    elif '*/' in line:
                        # 结束多行注释
                        in_multiline_comment = False
                        comment_lines.append(line)
                    elif in_multiline_comment:
                        # 多行注释内部
                        comment_lines.append(line)
                    else:
                        # SQL内容
                        sql_lines.append(line)
                
                # 添加多行注释
                if comment_lines:
                    for comment_line in comment_lines:
                        result_lines.append(base_indent + '  ' + comment_line)
                
                # 处理SQL内容
                if sql_lines:
                    sql_part = ' '.join(sql_lines).strip()
                    if sql_part:
                        if i < len(cols) - 1:
                            result_lines.append(base_indent + f'  {sql_part},')
                        else:
                            result_lines.append(base_indent + f'  {sql_part}')
                continue
            
            # 检查列中是否包含窗口函数 OVER(...)
            if 'OVER' in col.upper() and '(' in col:
                formatted_col = format_window_function(col, indent_level=0)
                # 如果是多行,需要特殊处理
                if '\n' in formatted_col:
                    col_lines = formatted_col.split('\n')
                    if i < len(cols) - 1:
                        # 不是最后一列,在最后一行加逗号
                        col_lines[-1] += ','
                    # 所有行都需要添加缩进
                    for line in col_lines:
                        result_lines.append(base_indent + '  ' + line)
                else:
                    if i < len(cols) - 1:
                        result_lines.append(base_indent + f'  {formatted_col},')
                    else:
                        result_lines.append(base_indent + f'  {formatted_col}')
            # 检查列中是否包含CASE表达式
            elif 'CASE' in col.upper():
                # 格式化CASE表达式
                formatted_case = format_case_expression(col, indent_level=indent_level + 1)
                if i < len(cols) - 1:
                    result_lines.append(formatted_case.rstrip() + ',')
                else:
                    result_lines.append(formatted_case)
            # 检查列中是否包含JSON_OBJECT
            elif 'JSON_OBJECT' in col.upper():
                formatted_col = format_json_object(col, indent_level=indent_level + 1)
                # 如果是多行,需要特殊处理
                if '\n' in formatted_col:
                    col_lines = formatted_col.split('\n')
                    if i < len(cols) - 1:
                        # 不是最后一列,在最后一行加逗号
                        col_lines[-1] += ','
                    # 所有行都已经包含了完整的绝对缩进，直接添加
                    for line in col_lines:
                        result_lines.append(line)
                else:
                    if i < len(cols) - 1:
                        result_lines.append(base_indent + f'  {col},')
                    else:
                        result_lines.append(base_indent + f'  {col}')
            else:
                # 普通列，移除函数括号前后的空格
                col = remove_space_before_paren(col)
                if i < len(cols) - 1:
                    result_lines.append(base_indent + f'  {col},')
                else:
                    result_lines.append(base_indent + f'  {col}')
        
        # 检查是否有注释在最后一列之后
        if len(cols) in inline_comments_by_col:
            result_lines.append(base_indent + '  ' + inline_comments_by_col[len(cols)])
    
    # FROM - 格式化JSON_TABLE
    from_clause = parts.get('from', '')
    if from_clause:
        result_lines.append(base_indent + 'FROM')
        # 格式化FROM子句，特别处理JSON_TABLE
        formatted_from = format_from_clause(from_clause, indent_level=indent_level)
        result_lines.extend(formatted_from)
    else:
        # 确保FROM子句存在
        if 'FROM' in statement.upper():
            # 直接从原始语句中提取FROM子句
            # 查找FROM关键字的位置（支持后面是空格或换行符）
            from_pos = -1
            for i in range(len(statement) - 4):
                if statement[i:i+4].upper() == 'FROM':
                    # 检查FROM后面的字符
                    if i + 4 < len(statement):
                        next_char = statement[i+4]
                        if next_char in [' ', '\n', '\r']:
                            from_pos = i
                            break
            
            if from_pos != -1:
                # 提取FROM子句直到遇到下一个关键字
                from_text = statement[from_pos+4:]
                # 查找下一个关键字
                keywords = ['WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT']
                end_pos = len(from_text)
                for kw in keywords:
                    pos = from_text.upper().find(' ' + kw + ' ')
                    if pos != -1 and pos < end_pos:
                        end_pos = pos
                    pos2 = from_text.upper().find('\n' + kw + ' ')
                    if pos2 != -1 and pos2 < end_pos:
                        end_pos = pos2
                    pos3 = from_text.upper().find('\r\n' + kw + ' ')
                    if pos3 != -1 and pos3 < end_pos:
                        end_pos = pos3
                from_text = from_text[:end_pos].strip()
                result_lines.append(base_indent + 'FROM')
                result_lines.append(base_indent + '  ' + from_text)
    
    # WHERE
    where_clause = parts.get('where', '')
    if where_clause:
        result_lines.append(base_indent + 'WHERE')
        where_conditions = split_and_conditions(where_clause)
        for i, cond in enumerate(where_conditions):
            # 跳过空条件
            if not cond.strip():
                continue
            
            # 如果整个条件就是注释，直接添加
            cond_stripped = cond.strip()
            if cond_stripped.startswith('--'):
                result_lines.append(base_indent + '  ' + cond_stripped)
                continue
            
            # 检查是否有行内注释（在split_and_conditions之前就要处理）
            inline_comment = ''
            if '--' in cond:
                # 找到注释的位置
                comment_pos = cond.find('--')
                inline_comment = cond[comment_pos:].strip()
                cond = cond[:comment_pos].strip()
            
            # 检查是否是嵌套括号条件（以(开头且包含嵌套括号）
            cond_stripped = cond.strip()
            if cond_stripped.startswith('(') and cond_stripped.endswith(')'):
                # 检查是否有嵌套括号或OR
                inner = cond_stripped[1:-1]
                has_nested_or_or = False
                depth = 0
                for idx, char in enumerate(inner):
                    if char == '(':
                        if depth == 0:
                            has_nested_or_or = True
                            break
                        depth += 1
                    elif char == ')':
                        depth -= 1
                    elif depth == 0 and inner[idx:idx+4].upper() == ' OR ':
                        has_nested_or_or = True
                        break
                
                if has_nested_or_or:
                    # 使用新的嵌套括号格式化函数
                    from .expression_formatters import format_nested_parentheses_condition
                    formatted_lines = format_nested_parentheses_condition(cond_stripped, base_indent + '  ')
                    if i == 0:
                        result_lines.extend(formatted_lines)
                    else:
                        # 第一行前面加上 and
                        if formatted_lines:
                            first_line = formatted_lines[0]
                            content = first_line.strip()
                            result_lines.append(base_indent + '  AND ' + content)
                            result_lines.extend(formatted_lines[1:])
                    continue
            
            # 普通条件处理
            # 移除函数名和左括号之间的空格
            cond = remove_space_before_paren(cond)
            # 确保等号周围有空格
            cond = add_space_around_equals(cond)
            # 格式化IN子句
            cond = format_in_clause(cond)
            
            # 如果条件包含换行（如格式化后的IN子句），需要特殊处理
            if '\n' in cond:
                cond_lines = cond.split('\n')
                if i == 0:
                    result_lines.append(base_indent + '  ' + cond_lines[0])
                else:
                    result_lines.append(base_indent + '  AND ' + cond_lines[0])
                # 其余行保持原有缩进
                for line in cond_lines[1:]:
                    result_lines.append(base_indent + '  ' + line)
                # 如果有行内注释，添加到最后
                if inline_comment:
                    result_lines.append(base_indent + '  ' + inline_comment)
            else:
                if i == 0:
                    # 如果有行内注释，条件和注释分别在不同行
                    result_lines.append(base_indent + '  ' + cond)
                    if inline_comment:
                        result_lines.append(base_indent + '  ' + inline_comment)
                else:
                    # 如果有行内注释，条件和注释分别在不同行
                    result_lines.append(base_indent + '  AND ' + cond)
                    if inline_comment:
                        result_lines.append(base_indent + '  ' + inline_comment)
    
    # GROUP BY
    groupby_clause = parts.get('group_by', '')
    if groupby_clause:
        result_lines.append(base_indent + 'GROUP BY')
        # 分割GROUP BY的列
        group_cols = split_columns(groupby_clause)
        for i, col in enumerate(group_cols):
            if i < len(group_cols) - 1:
                result_lines.append(base_indent + '  ' + col + ',')
            else:
                result_lines.append(base_indent + '  ' + col)
    
    # HAVING
    having_clause = parts.get('having', '')
    if having_clause:
        result_lines.append(base_indent + 'HAVING')
        having_conditions = split_and_conditions(having_clause)
        for i, cond in enumerate(having_conditions):
            # 确保等号和比较运算符周围有空格
            cond = add_space_around_equals(cond)
            if i == 0:
                result_lines.append(base_indent + '  ' + cond)
            else:
                result_lines.append(base_indent + '  AND ' + cond)
    
    # ORDER BY
    orderby_clause = parts.get('order_by', '')
    if orderby_clause:
        result_lines.append(base_indent + 'ORDER BY')
        # 分割ORDER BY的列
        order_cols = split_columns(orderby_clause)
        for i, col in enumerate(order_cols):
            if i < len(order_cols) - 1:
                result_lines.append(base_indent + '  ' + col + ',')
            else:
                result_lines.append(base_indent + '  ' + col)
    
    # LIMIT
    limit_value = parts.get('limit', '')
    if limit_value:
        result_lines.append(base_indent + 'LIMIT')
        result_lines.append(base_indent + '  ' + limit_value)
    
    # 添加分号（只在顶层且原始SQL有分号时）
    if indent_level == 0 and has_semicolon:
        result_lines[-1] += ';'
    
    # 处理剩余的SQL语句
    formatted = '\n'.join(result_lines)
    
    return formatted


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
        
        # 检查最后一行是否是GROUP BY，如果是，需要在它后面添加ON DUPLICATE KEY
        last_line = result_lines[-1].strip()
        if last_line.startswith('GROUP BY'):
            result_lines.append('  ' + last_line.split('GROUP BY')[1].strip() + ' ON DUPLICATE KEY')
            result_lines[-2] = 'GROUP BY'
        else:
            result_lines.append('ON DUPLICATE KEY')
        
        result_lines.append('UPDATE')
        
        for i, assignment in enumerate(update_assignments):
            # 确保等号周围有空格
            assignment = add_space_around_equals(assignment)
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
        
        # 分割列
        column_list = [col.strip() for col in columns.split(',')]
        
        # 构建结果 - INSERT INTO单独一行，表名和列缩进2个空格
        result_lines = ['INSERT INTO']
        result_lines.append(f'  {table_name} (')
        for i, col in enumerate(column_list):
            if i < len(column_list) - 1:
                result_lines.append(f'    {col},')
            else:
                result_lines.append(f'    {col}')
        result_lines.append('  )')
        
        # 格式化 SELECT 语句
        formatted_select = format_select(select_part, indent_level=0)
        result_lines.append(formatted_select)
        
        return '\n'.join(result_lines)
    
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
    
    # 构建结果 - INSERT INTO 换行，表名和列，VALUES 换行，每行值缩进2个空格
    result_lines = ['INSERT INTO']
    
    # 每个列单独一行
    result_lines.append(f'  {table_name} (')
    for i, col in enumerate(column_list):
        if i < len(column_list) - 1:
            result_lines.append(f'    {col},')
        else:
            result_lines.append(f'    {col}')
    result_lines.append('  )')
    
    result_lines.append('VALUES')
    
    # 每个值也单独一行
    for row_idx, row in enumerate(value_rows):
        # 提取括号内的值
        row_content = row.strip('()')
        row_values = [v.strip() for v in row_content.split(',')]
        
        result_lines.append('  (')
        for i, val in enumerate(row_values):
            if i < len(row_values) - 1:
                result_lines.append(f'    {val},')
            else:
                result_lines.append(f'    {val}')
        
        if row_idx < len(value_rows) - 1:
            result_lines.append('  ),')
        else:
            result_lines.append('  );')
    
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
    
    # 构建结果 - UPDATE单独一行，表名缩进2个空格
    result_lines = ['UPDATE']
    result_lines.append(f'  {table_name}')
    result_lines.append('SET')
    
    for i, assignment in enumerate(assignments):
        # 处理 CASE 语句
        if 'CASE' in assignment.upper():
            # 提取列名和CASE表达式
            # 格式: column_name = CASE ... END
            case_pos = assignment.upper().find('CASE')
            if case_pos > 0:
                # 有列名
                column_part = assignment[:case_pos].strip()
                case_part = assignment[case_pos:].strip()
                
                # 确保列名部分的等号周围有空格
                column_part = add_space_around_equals(column_part)
                
                formatted_case = format_case_expression(case_part, indent_level=1)
                # 将列名添加到CASE表达式的第一行（等号后有空格，CASE前没有空格）
                case_lines = formatted_case.split('\n')
                if case_lines:
                    # 移除column_part末尾的空格，然后直接连接CASE
                    case_lines[0] = f'  {column_part.rstrip()}{case_lines[0].strip()}'
                    formatted_assignment = '\n'.join(case_lines)
                else:
                    formatted_assignment = f'  {column_part.rstrip()}{formatted_case}'
            else:
                # 没有列名，直接格式化CASE
                formatted_case = format_case_expression(assignment, indent_level=1)
                formatted_assignment = formatted_case
            
            if i < len(assignments) - 1:
                result_lines.append(formatted_assignment.rstrip() + ',')
            else:
                result_lines.append(formatted_assignment)
        else:
            # 检查是否有行内注释
            inline_comment = ''
            if '--' in assignment:
                # 找到注释的位置
                comment_pos = assignment.find('--')
                inline_comment = assignment[comment_pos:].strip()
                assignment = assignment[:comment_pos].strip()
            
            # 确保等号周围有空格
            assignment = add_space_around_equals(assignment)
            
            # 如果有行内注释，在赋值后添加一个空格，然后注释单独一行
            if inline_comment:
                if i < len(assignments) - 1:
                    result_lines.append(f'  {assignment}, ')
                else:
                    result_lines.append(f'  {assignment} ')
                result_lines.append('  ' + inline_comment)
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
            # 确保等号周围有空格
            cond = add_space_around_equals(cond)
            
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


def format_delete(statement: str) -> str:
    """格式化 DELETE 语句"""
    # 保存原始语句用于比较
    original_statement = statement
    
    # 移除所有换行，变成一行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 提取表名和 WHERE - 使用更灵活的正则表达式匹配表名
    match = re.search(r'DELETE\s+FROM\s+([^\s]+)(?:\s+WHERE\s+(.*))?', statement, re.IGNORECASE | re.DOTALL)
    if not match:
        # 确保以分号结尾（如果原本没有）
        if not statement.endswith(';'):
            return statement + ';'
        return statement
    
    table_name = match.group(1)
    where_clause = match.group(2) if match.group(2) else ''
    
    # 构建结果 - DELETE FROM单独一行，表名缩进2个空格
    result_lines = ['DELETE FROM']
    result_lines.append(f'  {table_name}')
    
    # WHERE
    if where_clause:
        result_lines.append('WHERE')
        where_conditions = split_and_conditions(where_clause)
        for i, cond in enumerate(where_conditions):
            # 确保等号周围有空格
            cond = add_space_around_equals(cond)
            if i == 0:
                result_lines.append(f'  {cond}')
            else:
                result_lines.append(f'  AND {cond}')
    
    # 添加分号
    result_lines[-1] += ';'
    
    formatted_result = '\n'.join(result_lines)
    
    # 检查内容是否一致
    def normalize_content(content: str) -> str:
        """标准化SQL内容，移除所有空白字符用于比较"""
        return ''.join(content.split())
    
    if normalize_content(original_statement) != normalize_content(formatted_result):
        return original_statement
    
    return formatted_result


def format_union_query(statement: str, indent_level: int = 0) -> str:
    """
    格式化包含UNION ALL的查询
    
    Args:
        statement: 包含UNION ALL的SQL语句
        indent_level: 缩进级别（用于子查询）
        
    Returns:
        格式化后的语句
    """
    # 记录原始SQL是否有分号
    has_semicolon = statement.rstrip().endswith(';')
    
    # 移除所有换行
    statement = ' '.join(statement.split())
    
    # 移除分号
    statement = statement.rstrip(';').strip()
    
    # 按UNION ALL分割(考虑括号深度)
    parts = split_union_all(statement)
    
    # 格式化每个SELECT
    formatted_parts = []
    for i, part in enumerate(parts):
        formatted = format_select(part.strip(), indent_level=indent_level)
        # 移除SELECT部分的分号
        if formatted.endswith(';'):
            formatted = formatted[:-1]
        formatted_parts.append(formatted)
    
    # 用UNION ALL连接，添加适当的缩进
    base_indent = '  ' * indent_level
    union_separator = f'\n{base_indent}UNION ALL\n'
    result = union_separator.join(formatted_parts)
    
    # 只在原始SQL有分号时才添加分号
    if has_semicolon:
        result += ';'
    
    return result