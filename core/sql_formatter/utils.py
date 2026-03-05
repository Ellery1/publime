"""
SQL格式化器工具函数模块
"""

import re
from typing import Tuple


def extract_inline_comment(text: str) -> Tuple[str, str]:
    """
    从文本中提取行尾注释
    
    Args:
        text: 可能包含注释的文本
        
    Returns:
        (代码部分, 注释部分) 的元组
        
    Example:
        >>> extract_inline_comment("u.is_active=1 -- 只统计活跃用户")
        ("u.is_active=1", "-- 只统计活跃用户")
        >>> extract_inline_comment("SELECT * FROM users")
        ("SELECT * FROM users", "")
    """
    # 查找 -- 注释（单行注释）
    comment_pos = text.find('--')
    if comment_pos != -1:
        code = text[:comment_pos].strip()
        comment = text[comment_pos:].strip()
        return (code, comment)
    
    # 查找 /* */ 注释（行尾的多行注释）
    comment_start = text.rfind('/*')
    if comment_start != -1:
        comment_end = text.find('*/', comment_start)
        if comment_end != -1:
            code = text[:comment_start].strip()
            comment = text[comment_start:comment_end+2].strip()
            return (code, comment)
    
    return (text.strip(), '')


def compress_sql_preserving_comments(statement: str) -> str:
    """
    压缩SQL语句，但保留注释的换行符
    
    Args:
        statement: SQL语句
        
    Returns:
        压缩后的SQL语句
        
    Strategy:
        1. 按行分割
        2. 对于每一行：
           - 如果是纯注释行，保留换行符
           - 如果包含行尾注释，保留换行符
           - 否则，移除换行符
        3. 用空格连接
    """
    lines = statement.split('\n')
    result_parts = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # 纯注释行
        if stripped.startswith('--') or stripped.startswith('/*'):
            # 保留注释，添加换行符标记
            if result_parts and result_parts[-1] != '\n':
                result_parts.append('\n')
            result_parts.append(stripped)
            result_parts.append('\n')
        # 包含行尾注释
        elif '--' in stripped or '/*' in stripped:
            code, comment = extract_inline_comment(stripped)
            if code:
                result_parts.append(code)
            if comment:
                result_parts.append('\n')
                result_parts.append(comment)
                result_parts.append('\n')
        else:
            result_parts.append(stripped)
    
    return ' '.join(result_parts)


def separate_keywords(text: str) -> str:
    """
    分离关键字，在关键字前后添加空格，并将关键字转换为大写
    
    Args:
        text: SQL文本
        
    Returns:
        分离关键字后的文本
    """
    # print(f"[DEBUG] separate_keywords输入: {text}")
    
    # 按照从长到短的顺序处理，避免冲突
    # 使用负向前瞻(?![^(]*\))确保只在括号外处理关键字
    # 将关键字转换为大写
    keywords_patterns = [
        # 独立的关键字（前后有空格或边界）
        (r'(?i)(?<![a-zA-Z0-9_])(select)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # select -> SELECT
        (r'(?i)(?<![a-zA-Z0-9_])(from)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # from -> FROM
        (r'(?i)(?<![a-zA-Z0-9_])(where)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # where -> WHERE
        (r'(?i)(?<![a-zA-Z0-9_])(and)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # and -> AND
        (r'(?i)(?<![a-zA-Z0-9_])(or)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # or -> OR
        (r'(?i)(?<![a-zA-Z0-9_])(group\s*by)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # group by -> GROUP BY
        (r'(?i)(?<![a-zA-Z0-9_])(order\s*by)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # order by -> ORDER BY
        (r'(?i)(?<![a-zA-Z0-9_])(union\s*all)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # union all -> UNION ALL
        (r'(?i)(?<![a-zA-Z0-9_])(union)(?![a-zA-Z0-9_])', lambda m: m.group(1).upper()),  # union -> UNION
        # 关键字前后有其他字符的情况
        (r'(?i)(?![^(]*\))([0-9])(union)(?![a-zA-Z0-9_])', lambda m: m.group(1) + ' ' + m.group(2).upper()),  # 1union -> 1 UNION
        (r'(?i)(?![^(]*\))([0-9a-zA-Z_]+)(select)(?=\s|[a-zA-Z0-9_]|$)', lambda m: m.group(1) + ' ' + m.group(2).upper()),  # xselect -> x SELECT
        (r'(?i)(?![^(]*\))(select)([a-zA-Z0-9_]+)(?=\s|[a-zA-Z0-9_]|$)', lambda m: m.group(1).upper() + ' ' + m.group(2)),  # selectx -> SELECT x
        (r'(?i)(?![^(]*\))([0-9a-zA-Z_]+)(from)(?=\s|[a-zA-Z0-9_]|$)', lambda m: m.group(1) + ' ' + m.group(2).upper()),  # xfrom -> x FROM
        (r'(?i)(?![^(]*\))(from)([a-zA-Z0-9_]+)(?=\s|[a-zA-Z0-9_]|$)', lambda m: m.group(1).upper() + ' ' + m.group(2)),  # fromx -> FROM x
        (r'(?i)(?![^(]*\))([0-9a-zA-Z_]+)(where)(?=\s|[a-zA-Z0-9_]|$)', lambda m: m.group(1) + ' ' + m.group(2).upper()),  # xwhere -> x WHERE
        (r'(?i)(?![^(]*\))(where)([a-zA-Z0-9_]+)(?=\s|[a-zA-Z0-9_]|$)', lambda m: m.group(1).upper() + ' ' + m.group(2)),  # wherex -> WHERE x
    ]
    
    result = text
    for pattern, replacement in keywords_patterns:
        result = re.sub(pattern, replacement, result)
    
    # 清理多余空格（只清理连续的多个空格，保留单个空格）
    result = re.sub(r' {2,}', ' ', result)
    
    # print(f"[DEBUG] separate_keywords输出: {result}")
    
    return result


def compact_json_table(text: str) -> str:
    """
    压缩JSON_TABLE函数,移除 ) ) 之间的空格变成 ))
    
    Args:
        text: SQL文本
        
    Returns:
        压缩后的文本
    """
    # 找到JSON_TABLE并移除结尾的 ) ) 变成 ))
    # 使用更精确的模式匹配JSON_TABLE的完整结构
    pattern = r'(JSON_TABLE\s*\([^)]*\([^)]*\)[^)]*)\)\s+\)'
    
    def compress_match(match):
        # 保留第一部分，然后添加 )) 而不是 ) )
        return match.group(1) + '))'
    
    result = re.sub(pattern, compress_match, text, flags=re.DOTALL)
    return result


def add_space_after_comma(text: str) -> str:
    """
    在函数调用的逗号后添加空格
    
    Args:
        text: SQL文本
        
    Returns:
        处理后的文本
    """
    # 在逗号后添加空格（如果后面不是空格或换行）
    # 使用正则表达式：逗号后面不是空格、换行或右括号时，添加空格
    text = re.sub(r',(?=[^\s\n)])', r', ', text)
    
    return text


def add_space_around_equals(text: str) -> str:
    """
    在等号、不等号和比较运算符前后添加空格
    
    Args:
        text: SQL文本
        
    Returns:
        处理后的文本
    """
    # 特殊处理：在等号后面跟CASE关键字的情况
    text = re.sub(r'(?i)=(?=case)', r' = CASE', text)
    
    # 在 != 前后添加空格
    text = re.sub(r'!=', r' != ', text)
    text = re.sub(r'\s+!=\s+', r' != ', text)
    
    # 在 >= 和 <= 前后添加空格
    text = re.sub(r'>=', r' >= ', text)
    text = re.sub(r'\s+>=\s+', r' >= ', text)
    text = re.sub(r'<=', r' <= ', text)
    text = re.sub(r'\s+<=\s+', r' <= ', text)
    
    # 在 > 和 < 前后添加空格（但要避免已经处理过的 >= 和 <=）
    text = re.sub(r'(?<![<>=])>(?!=)', r' > ', text)
    text = re.sub(r'\s+>\s+', r' > ', text)
    text = re.sub(r'(?<![<>=])<(?!=)', r' < ', text)
    text = re.sub(r'\s+<\s+', r' < ', text)
    
    # 在等号前后添加空格（但要避免处理 >=, <=, !=）
    text = re.sub(r'(?<![!<>])=(?!=)', r' = ', text)
    text = re.sub(r'\s+=\s+', r' = ', text)
    
    return text


def format_in_clause(condition: str) -> str:
    """
    格式化IN子句，将值换行
    例如: col in('a', 'b', 'c') -> col in(\n  'a',\n  'b',\n  'c'\n)
    对于子查询: col IN(SELECT ...) -> 保持不变（由调用者处理）
    
    Args:
        condition: 包含IN子句的条件
        
    Returns:
        格式化后的条件
    """
    import re
    
    # 查找IN子句 - 支持表名前缀（如t1.column）和NOT IN
    # 先尝试匹配 NOT IN
    match = re.search(r'([\w.]+)\s+(not\s+in)\s*\((.*?)\)', condition, re.IGNORECASE | re.DOTALL)
    if not match:
        # 如果没有NOT IN，尝试匹配普通的IN
        match = re.search(r'([\w.]+)\s+(in)\s*\((.*?)\)', condition, re.IGNORECASE | re.DOTALL)
    
    if not match:
        return condition
    
    column = match.group(1)
    in_keyword = match.group(2)  # 保留原始大小写
    values_text = match.group(3)
    
    # 检查是否是子查询（包含SELECT关键字）
    if 'SELECT' in values_text.upper():
        # 这是一个子查询，不在这里处理，返回原始条件
        return condition
    
    # 分割值（按逗号，但要考虑字符串）
    values = []
    current = ''
    in_string = False
    string_char = None
    
    for char in values_text:
        if char in ('"', "'") and not in_string:
            in_string = True
            string_char = char
            current += char
        elif char == string_char and in_string:
            in_string = False
            string_char = None
            current += char
        elif char == ',' and not in_string:
            values.append(current.strip())
            current = ''
        else:
            current += char
    
    if current.strip():
        values.append(current.strip())
    
    # 如果只有1-2个值，不换行
    if len(values) <= 2:
        # 移除每个值前后的空格
        cleaned_values = [v.strip() for v in values]
        # IN关键字后有空格
        return f'{column} {in_keyword} ({", ".join(cleaned_values)})'
    
    # 如果值较少（3-5个），也不换行
    if len(values) <= 5:
        cleaned_values = [v.strip() for v in values]
        return f'{column} {in_keyword} ({", ".join(cleaned_values)})'
    
    # 构建格式化的IN子句（超过5个值才换行）
    result = f'{column} {in_keyword} (\n'
    for i, value in enumerate(values):
        if i < len(values) - 1:
            result += f'  {value},\n'
        else:
            result += f'  {value}\n'
    result += ')'
    
    return result



def remove_space_before_paren(text: str) -> str:
    """
    移除函数名和左括号之间的空格，以及左括号后的空格，以及右括号前的空格
    但确保IN/NOT IN关键字后有空格（不区分大小写）
    例如: DATE_FORMAT ( -> DATE_FORMAT(
          DATE_FORMAT( -> DATE_FORMAT(
          DATE_FORMAT( trsdat ) -> DATE_FORMAT(trsdat)
          IN (3) -> IN (3)  # 保留IN后的空格
          IN(3) -> IN (3)   # 添加IN后的空格
          in (3) -> in (3)  # 保留in后的空格
          in(3) -> in (3)   # 添加in后的空格
    
    Args:
        text: 输入文本
        
    Returns:
        处理后的文本
    """
    import re
    
    # 第一步：确保IN/NOT IN关键字后有空格（不区分大小写）
    # 匹配 IN( 或 in( 等，添加空格
    text = re.sub(r'\b(IN|in|In|iN)\(', r'\1 (', text)
    text = re.sub(r'\b(NOT\s+IN|not\s+in|Not\s+In|NOT\s+in|not\s+IN)\(', r'\1 (', text, flags=re.IGNORECASE)
    
    # 第二步：保护IN/NOT IN关键字后的空格，用特殊标记替换
    text = re.sub(r'\b(IN|in|In|iN)\s+\(', r'\1<<<SPACE>>>(', text)
    text = re.sub(r'\b(NOT\s+IN|not\s+in|Not\s+In|NOT\s+in|not\s+IN)\s+\(', r'\1<<<SPACE>>>(', text, flags=re.IGNORECASE)
    
    # 第三步：移除其他函数名后的空格
    # 匹配函数名（字母、数字、下划线）后跟空格和左括号
    text = re.sub(r'(\w+)\s+\(', r'\1(', text)
    # 匹配左括号后的空格
    text = re.sub(r'\(\s+', '(', text)
    # 匹配右括号前的空格
    text = re.sub(r'\s+\)', ')', text)
    
    # 第四步：恢复IN/NOT IN关键字后的空格
    text = text.replace('<<<SPACE>>>', ' ')
    
    return text