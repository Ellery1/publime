"""
SQL格式化器表达式格式化模块

包含CASE表达式、FROM子句、JSON_TABLE、WITH子句等格式化函数
"""

import re
from typing import List


def format_in_subquery(condition: str, indent_level: int) -> str:
    """
    格式化IN子句中的子查询
    例如: user_id IN(SELECT user_id FROM ...) -> user_id IN(\n  SELECT ...\n)
    
    Args:
        condition: 包含IN子句的条件
        indent_level: 缩进级别
        
    Returns:
        格式化后的条件
    """
    # 找到所有IN子句的位置
    positions = []
    i = 0
    while i < len(condition):
        # 查找IN关键字
        in_match = re.search(r'([\w.]+)\s+((?:NOT\s+)?IN)\s*\(', condition[i:], re.IGNORECASE)
        if not in_match:
            break
        
        # 计算绝对位置
        match_start = i + in_match.start()
        match_end = i + in_match.end()
        
        # 提取列名和IN关键字
        column = in_match.group(1)
        in_keyword = in_match.group(2)
        
        # 找到左括号
        paren_start = condition.find('(', match_end - 1)
        if paren_start == -1:
            i = match_end
            continue
        
        # 找到对应的右括号
        depth = 1
        j = paren_start + 1
        while j < len(condition) and depth > 0:
            if condition[j] == '(':
                depth += 1
            elif condition[j] == ')':
                depth -= 1
            j += 1
        
        # 检查括号内是否包含SELECT
        inner_content = condition[paren_start+1:j-1].strip()
        if 'SELECT' in inner_content.upper():
            positions.append((match_start, paren_start, j, column, in_keyword))
        
        i = j
    
    # 从后往前替换，避免位置偏移
    for start, paren_start, end, column, in_keyword in reversed(positions):
        # 提取子查询内容（去掉括号）
        inner_content = condition[paren_start+1:end-1].strip()
        
        # 格式化子查询
        from .formatters import format_select
        # 格式化子查询内容
        formatted_select = format_select(inner_content, indent_level=0)
        
        # 添加缩进（子查询内容缩进indent_level + 1）
        select_lines = formatted_select.split('\n')
        indented_lines = [('  ' * (indent_level + 1)) + line for line in select_lines]
        indented_select = '\n'.join(indented_lines)
        
        # 构建替换文本（IN关键字后有空格，子查询格式化并缩进）
        replacement = f'{column} {in_keyword} (\n{indented_select}\n' + ('  ' * indent_level) + ')'
        
        # 替换
        condition = condition[:start] + replacement + condition[end:]
    
    return condition


def format_case_expression(expression: str, indent_level: int = 0) -> str:
    """格式化 CASE 表达式

    Args:
        expression: CASE 表达式
        indent_level: 缩进级别

    Returns:
        格式化后的 CASE 表达式
    """
    # 首先提取 AS 子句（在调用separate_keywords之前，以保留原始大小写）
    as_match = re.search(r'(?i)\s+AS\s+\w+', expression)
    if as_match:
        as_clause = as_match.group(0)
        # 保持AS关键字的原始大小写
        # 只清理多余空格
        as_clause = ' '.join(as_clause.split())
        # 确保前面有空格
        if not as_clause.startswith(' '):
            as_clause = ' ' + as_clause
        case_body = expression[:as_match.start()].strip()
    else:
        as_clause = ''
        case_body = expression.strip()
    
    from .utils import separate_keywords
    # 分离关键字，解决如country_rankFROM这样的问题
    # 注意：只对case_body调用，不对as_clause调用，以保留AS的原始大小写
    case_body = separate_keywords(case_body)

    # 移除 CASE 关键字
    if case_body.upper().startswith('CASE'):
        case_body = case_body[4:].strip()

    # 定义缩进
    base_indent = '  ' * indent_level
    item_indent = '  ' * (indent_level + 1)

    lines = []
    lines.append(f'{base_indent}CASE')

    i = 0
    while i < len(case_body):
        # 跳过空白
        while i < len(case_body) and case_body[i].isspace():
            i += 1

        # 检查 WHEN
        if case_body[i:i+4].upper() == 'WHEN':
            i += 4
            # 跳过空白
            while i < len(case_body) and case_body[i].isspace():
                i += 1

            # 提取条件（直到 THEN）
            condition = ''
            depth = 0
            while i < len(case_body):
                if case_body[i] == '(':
                    depth += 1
                    condition += case_body[i]
                elif case_body[i] == ')':
                    depth -= 1
                    condition += case_body[i]
                elif depth == 0 and case_body[i:i+5].upper() == ' THEN':
                    break
                else:
                    condition += case_body[i]
                i += 1

            # 跳过 THEN（包括前面的空格，共5个字符）
            i += 5
            # 跳过空白
            while i < len(case_body) and case_body[i].isspace():
                i += 1

            # 提取结果（直到下一个 WHEN/ELSE/END）
            result = ''
            depth = 0
            in_string = False
            string_char = ''
            while i < len(case_body):
                char = case_body[i]
                
                # 处理字符串
                if char in ('"', "'"):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                    result += char
                elif not in_string:
                    if char == '(':
                        depth += 1
                        result += char
                    elif char == ')':
                        depth -= 1
                        result += char
                    elif depth == 0:
                        # 检查下一个关键字
                        next_keyword = case_body[i:i+5].upper()
                        if next_keyword.startswith('WHEN ') or next_keyword.startswith('ELSE '):
                            break
                        # 检查END关键字（需要确保是完整的单词）
                        if case_body[i:i+4].upper() == 'END ' or case_body[i:i+4].upper() == 'END\n' or case_body[i:i+4].upper() == 'END\r':
                            break
                        if case_body[i:i+3].upper() == 'END' and i + 3 >= len(case_body):
                            break
                        result += char
                    else:
                        result += char
                else:
                    result += char
                i += 1

            # 格式化条件:将AND分割到多行
            condition = condition.strip()
            # 在分割之前，确保等号周围有空格
            from .utils import add_space_around_equals, format_in_clause
            condition = add_space_around_equals(condition)

            # 检查并格式化IN子句中的子查询
            condition = format_in_subquery(condition, indent_level=indent_level + 1)

            # 格式化IN子句（值列表）
            condition = format_in_clause(condition)

            # 格式化结果
            result = result.strip()

            # 将AND关键字转换为大写
            condition = re.sub(r'(?i)\s+AND\s+', ' AND ', condition)
            # 将OR关键字转换为大写
            condition = re.sub(r'(?i)\s+OR\s+', ' OR ', condition)

            # 分割多个AND条件到多行
            # 使用正则表达式分割，但要考虑括号内的AND不应该分割
            and_parts = []
            current_part = ''
            depth = 0
            i_cond = 0
            while i_cond < len(condition):
                char = condition[i_cond]
                if char == '(':
                    depth += 1
                    current_part += char
                elif char == ')':
                    depth -= 1
                    current_part += char
                elif depth == 0 and condition[i_cond:i_cond+5] == ' AND ':
                    # 找到顶层的AND
                    and_parts.append(current_part.strip())
                    current_part = ''
                    i_cond += 5  # 跳过' AND '
                    continue
                else:
                    current_part += char
                i_cond += 1

            if current_part.strip():
                and_parts.append(current_part.strip())
            
            # 对每个AND部分，检查是否包含顶层的OR（不在括号内）
            # 如果有，也需要分割
            expanded_parts = []
            for and_part in and_parts:
                # 检查是否包含顶层OR
                has_top_level_or = False
                depth = 0
                i_check = 0
                while i_check < len(and_part):
                    if and_part[i_check] == '(':
                        depth += 1
                    elif and_part[i_check] == ')':
                        depth -= 1
                    elif depth == 0 and and_part[i_check:i_check+4] == ' OR ':
                        has_top_level_or = True
                        break
                    i_check += 1
                
                if has_top_level_or:
                    # 分割OR条件
                    or_parts = []
                    current_or_part = ''
                    depth = 0
                    i_or = 0
                    while i_or < len(and_part):
                        char = and_part[i_or]
                        if char == '(':
                            depth += 1
                            current_or_part += char
                        elif char == ')':
                            depth -= 1
                            current_or_part += char
                        elif depth == 0 and and_part[i_or:i_or+4] == ' OR ':
                            # 找到顶层的OR
                            or_parts.append(current_or_part.strip())
                            current_or_part = ''
                            i_or += 4  # 跳过' OR '
                            continue
                        else:
                            current_or_part += char
                        i_or += 1
                    
                    if current_or_part.strip():
                        or_parts.append(current_or_part.strip())
                    
                    # 将OR条件标记为特殊类型
                    expanded_parts.append({'type': 'or_group', 'parts': or_parts})
                else:
                    # 没有顶层OR，保持原样
                    expanded_parts.append({'type': 'simple', 'text': and_part})
            
            # 替换and_parts为expanded_parts
            and_parts = expanded_parts

            # 处理每个AND条件，检查是否包含括号内的OR
            formatted_and_parts = []
            for part in and_parts:
                # 检查part的类型
                if isinstance(part, dict):
                    if part['type'] == 'or_group':
                        # 这是一个OR组，需要分行显示
                        formatted_and_parts.append(part)
                        continue
                    elif part['type'] == 'simple':
                        part_text = part['text']
                    else:
                        # 未知类型，保持原样
                        formatted_and_parts.append(part)
                        continue
                else:
                    # 旧格式，字符串
                    part_text = part
                
                # 检查这个条件是否包含括号，且括号内有OR
                if '(' in part_text and ')' in part_text:
                    # 提取括号内的内容
                    paren_start = part_text.find('(')
                    paren_end = part_text.rfind(')')
                    
                    if paren_start != -1 and paren_end != -1 and paren_end > paren_start:
                        before_paren = part_text[:paren_start].rstrip()  # 使用rstrip()移除尾随空格
                        inside_paren = part_text[paren_start+1:paren_end].strip()
                        after_paren = part_text[paren_end+1:].strip()
                        
                        # 检查括号内是否包含OR（深度0的OR）
                        has_or = False
                        depth = 0
                        i_check = 0
                        while i_check < len(inside_paren):
                            if inside_paren[i_check] == '(':
                                depth += 1
                            elif inside_paren[i_check] == ')':
                                depth -= 1
                            elif depth == 0:
                                # 检查OR（大小写不敏感）
                                if i_check + 4 <= len(inside_paren):
                                    potential_or = inside_paren[i_check:i_check+4]
                                    if potential_or.upper() == ' OR ':
                                        has_or = True
                                        break
                            i_check += 1
                        
                        if has_or:
                            # 分割括号内的OR条件
                            or_parts = []
                            current_or_part = ''
                            depth = 0
                            i_or = 0
                            while i_or < len(inside_paren):
                                char = inside_paren[i_or]
                                if char == '(':
                                    depth += 1
                                    current_or_part += char
                                elif char == ')':
                                    depth -= 1
                                    current_or_part += char
                                elif depth == 0:
                                    # 检查OR（大小写不敏感）
                                    if i_or + 4 <= len(inside_paren):
                                        potential_or = inside_paren[i_or:i_or+4]
                                        if potential_or.upper() == ' OR ':
                                            # 找到顶层的OR
                                            or_parts.append(current_or_part.strip())
                                            current_or_part = ''
                                            i_or += 4  # 跳过' OR '
                                            continue
                                    current_or_part += char
                                else:
                                    current_or_part += char
                                i_or += 1
                            
                            if current_or_part.strip():
                                or_parts.append(current_or_part.strip())
                            
                            # 格式化为多行：before_paren (换行，or条件缩进，换行) after_paren
                            formatted_part = {
                                'type': 'paren_or',
                                'before': before_paren,
                                'or_parts': or_parts,
                                'after': after_paren
                            }
                            formatted_and_parts.append(formatted_part)
                        else:
                            # 括号内没有OR，保持原样
                            formatted_and_parts.append({'type': 'simple', 'text': part_text})
                    else:
                        # 括号不完整，保持原样
                        formatted_and_parts.append({'type': 'simple', 'text': part_text})
                else:
                    # 没有括号，保持原样
                    formatted_and_parts.append({'type': 'simple', 'text': part_text})

            # 检测THEN后的结果是否包含JSON_OBJECT
            if result.upper().startswith('JSON_OBJECT'):
                # 调用format_json_object进行格式化
                formatted_json = format_json_object(result, indent_level=indent_level + 1)
                # 分割成行
                json_lines = formatted_json.split('\n')
                # 第一行应该是 "  JSON_OBJECT(" (带缩进)，我们需要去掉缩进只保留 "JSON_OBJECT("
                first_line = json_lines[0].strip()

                # 输出WHEN条件
                if len(formatted_and_parts) == 1:
                    # 只有一个条件
                    part = formatted_and_parts[0]
                    if part['type'] == 'paren_or':
                        # 括号内有OR，需要多行格式化
                        if part["before"]:
                            lines.append(f'{item_indent}WHEN {part["before"]} (')
                        else:
                            lines.append(f'{item_indent}WHEN (')
                        # 输出OR条件，每个缩进
                        for k, or_part in enumerate(part['or_parts']):
                            if k == 0:
                                lines.append(f'{item_indent}  {or_part}')
                            else:
                                lines.append(f'{item_indent}  or {or_part}')
                        # 输出结束括号和THEN
                        if part['after']:
                            lines.append(f'{item_indent}) {part["after"]} THEN {first_line}')
                        else:
                            lines.append(f'{item_indent}) THEN {first_line}')
                    elif part['type'] == 'or_group':
                        # 顶层OR条件，需要分行
                        for k, or_part in enumerate(part['parts']):
                            if k == 0:
                                lines.append(f'{item_indent}WHEN {or_part}')
                            elif k == len(part['parts']) - 1:
                                # 最后一个OR条件，THEN在同一行
                                lines.append(f'{item_indent}OR {or_part} THEN {first_line}')
                            else:
                                lines.append(f'{item_indent}OR {or_part}')
                    else:
                        # 简单条件，直接输出
                        lines.append(f'{item_indent}WHEN {part["text"]} THEN {first_line}')
                else:
                    # 多个条件
                    for j, part in enumerate(formatted_and_parts):
                        if j == 0:
                            # 第一个条件在WHEN同一行
                            if part['type'] == 'paren_or':
                                if part["before"]:
                                    lines.append(f'{item_indent}WHEN {part["before"]} (')
                                else:
                                    lines.append(f'{item_indent}WHEN (')
                                for k, or_part in enumerate(part['or_parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}  {or_part}')
                                    else:
                                        lines.append(f'{item_indent}  or {or_part}')
                                if part['after']:
                                    lines.append(f'{item_indent}) {part["after"]}')
                                else:
                                    lines.append(f'{item_indent})')
                            elif part['type'] == 'or_group':
                                # 顶层OR条件
                                for k, or_part in enumerate(part['parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}WHEN {or_part}')
                                    else:
                                        lines.append(f'{item_indent}OR {or_part}')
                            else:
                                lines.append(f'{item_indent}WHEN {part["text"]}')
                        elif j == len(formatted_and_parts) - 1:
                            # 最后一个条件和THEN在同一行
                            if part['type'] == 'paren_or':
                                if part["before"]:
                                    lines.append(f'{item_indent}AND {part["before"]} (')
                                else:
                                    lines.append(f'{item_indent}AND (')
                                for k, or_part in enumerate(part['or_parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}  {or_part}')
                                    else:
                                        lines.append(f'{item_indent}  or {or_part}')
                                if part['after']:
                                    lines.append(f'{item_indent}) {part["after"]} THEN {first_line}')
                                else:
                                    lines.append(f'{item_indent}) THEN {first_line}')
                            elif part['type'] == 'or_group':
                                # 顶层OR条件，最后一个OR和THEN在同一行
                                for k, or_part in enumerate(part['parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}AND {or_part}')
                                    elif k == len(part['parts']) - 1:
                                        lines.append(f'{item_indent}OR {or_part} THEN {first_line}')
                                    else:
                                        lines.append(f'{item_indent}OR {or_part}')
                            else:
                                lines.append(f'{item_indent}AND {part["text"]} THEN {first_line}')
                        else:
                            # 中间的条件
                            if part['type'] == 'paren_or':
                                if part["before"]:
                                    lines.append(f'{item_indent}AND {part["before"]} (')
                                else:
                                    lines.append(f'{item_indent}AND (')
                                for k, or_part in enumerate(part['or_parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}  {or_part}')
                                    else:
                                        lines.append(f'{item_indent}  or {or_part}')
                                if part['after']:
                                    lines.append(f'{item_indent}) {part["after"]}')
                                else:
                                    lines.append(f'{item_indent})')
                            elif part['type'] == 'or_group':
                                # 顶层OR条件
                                for k, or_part in enumerate(part['parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}AND {or_part}')
                                    else:
                                        lines.append(f'{item_indent}OR {or_part}')
                            else:
                                lines.append(f'{item_indent}AND {part["text"]}')

                # 添加JSON_OBJECT的其余行（这些行已经包含了完整的绝对缩进）
                for json_line in json_lines[1:]:
                    lines.append(json_line)
            else:
                # 不包含JSON_OBJECT，使用原来的格式
                if len(formatted_and_parts) == 1:
                    # 只有一个条件
                    part = formatted_and_parts[0]
                    if part['type'] == 'paren_or':
                        # 括号内有OR，需要多行格式化
                        if part["before"]:
                            lines.append(f'{item_indent}WHEN {part["before"]} (')
                        else:
                            lines.append(f'{item_indent}WHEN (')
                        for k, or_part in enumerate(part['or_parts']):
                            if k == 0:
                                lines.append(f'{item_indent}  {or_part}')
                            else:
                                lines.append(f'{item_indent}  or {or_part}')
                        if part['after']:
                            lines.append(f'{item_indent}) {part["after"]} THEN {result}')
                        else:
                            lines.append(f'{item_indent}) THEN {result}')
                    elif part['type'] == 'or_group':
                        # 顶层OR条件，需要分行
                        for k, or_part in enumerate(part['parts']):
                            if k == 0:
                                lines.append(f'{item_indent}WHEN {or_part}')
                            elif k == len(part['parts']) - 1:
                                # 最后一个OR条件，THEN在同一行
                                lines.append(f'{item_indent}OR {or_part} THEN {result}')
                            else:
                                lines.append(f'{item_indent}OR {or_part}')
                    else:
                        # 简单条件，直接输出
                        lines.append(f'{item_indent}WHEN {part["text"]} THEN {result}')
                else:
                    # 多个条件
                    for j, part in enumerate(formatted_and_parts):
                        if j == 0:
                            # 第一个条件在WHEN同一行
                            if part['type'] == 'paren_or':
                                if part["before"]:
                                    lines.append(f'{item_indent}WHEN {part["before"]} (')
                                else:
                                    lines.append(f'{item_indent}WHEN (')
                                for k, or_part in enumerate(part['or_parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}  {or_part}')
                                    else:
                                        lines.append(f'{item_indent}  or {or_part}')
                                if part['after']:
                                    lines.append(f'{item_indent}) {part["after"]}')
                                else:
                                    lines.append(f'{item_indent})')
                            elif part['type'] == 'or_group':
                                # 顶层OR条件
                                for k, or_part in enumerate(part['parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}WHEN {or_part}')
                                    else:
                                        lines.append(f'{item_indent}OR {or_part}')
                            else:
                                lines.append(f'{item_indent}WHEN {part["text"]}')
                        elif j == len(formatted_and_parts) - 1:
                            # 最后一个条件和THEN在同一行
                            if part['type'] == 'paren_or':
                                if part["before"]:
                                    lines.append(f'{item_indent}AND {part["before"]} (')
                                else:
                                    lines.append(f'{item_indent}AND (')
                                for k, or_part in enumerate(part['or_parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}  {or_part}')
                                    else:
                                        lines.append(f'{item_indent}  or {or_part}')
                                if part['after']:
                                    lines.append(f'{item_indent}) {part["after"]} THEN {result}')
                                else:
                                    lines.append(f'{item_indent}) THEN {result}')
                            elif part['type'] == 'or_group':
                                # 顶层OR条件，最后一个OR和THEN在同一行
                                for k, or_part in enumerate(part['parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}AND {or_part}')
                                    elif k == len(part['parts']) - 1:
                                        lines.append(f'{item_indent}OR {or_part} THEN {result}')
                                    else:
                                        lines.append(f'{item_indent}OR {or_part}')
                            else:
                                lines.append(f'{item_indent}AND {part["text"]} THEN {result}')
                        else:
                            # 中间的条件
                            if part['type'] == 'paren_or':
                                if part["before"]:
                                    lines.append(f'{item_indent}AND {part["before"]} (')
                                else:
                                    lines.append(f'{item_indent}AND (')
                                for k, or_part in enumerate(part['or_parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}  {or_part}')
                                    else:
                                        lines.append(f'{item_indent}  or {or_part}')
                                if part['after']:
                                    lines.append(f'{item_indent}) {part["after"]}')
                                else:
                                    lines.append(f'{item_indent})')
                            elif part['type'] == 'or_group':
                                # 顶层OR条件
                                for k, or_part in enumerate(part['parts']):
                                    if k == 0:
                                        lines.append(f'{item_indent}AND {or_part}')
                                    else:
                                        lines.append(f'{item_indent}OR {or_part}')
                            else:
                                lines.append(f'{item_indent}AND {part["text"]}')

        # 检查 ELSE
        elif case_body[i:i+4].upper() == 'ELSE':
            i += 4
            # 跳过空白
            while i < len(case_body) and case_body[i].isspace():
                i += 1

            # 提取 ELSE 值（直到 END）
            else_value = ''
            depth = 0
            in_string = False
            string_char = ''
            while i < len(case_body):
                char = case_body[i]
                
                # 处理字符串
                if char in ('"', "'"):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                    else_value += char
                elif not in_string:
                    if char == '(':
                        depth += 1
                        else_value += char
                    elif char == ')':
                        depth -= 1
                        else_value += char
                    elif depth == 0:
                        # 检查END关键字（需要确保是完整的单词）
                        if case_body[i:i+3].upper() == 'END':
                            # 检查END后面是否是空格、逗号或结束
                            if i + 3 >= len(case_body) or case_body[i+3] in (' ', ',', '\n', '\r', '\t', ')'):
                                break
                        else_value += char
                    else:
                        else_value += char
                else:
                    else_value += char
                i += 1

            else_value = else_value.strip()

            # 检测ELSE后的结果是否包含JSON_OBJECT
            if else_value.upper().startswith('JSON_OBJECT'):
                # 调用format_json_object进行格式化
                formatted_json = format_json_object(else_value, indent_level=indent_level + 1)
                # 移除第一行的缩进，因为我们要把它放在ELSE后面
                json_lines = formatted_json.split('\n')
                first_line = json_lines[0].strip()
                lines.append(f'{item_indent}ELSE {first_line}')
                # 添加JSON_OBJECT的其余行
                for json_line in json_lines[1:]:
                    lines.append(json_line)
            else:
                lines.append(f'{item_indent}ELSE {else_value}')

        # 检查 END
        elif case_body[i:i+3].upper() == 'END':
            break
        else:
            i += 1

    lines.append(f'{base_indent}END{as_clause}')

    return '\n'.join(lines)



def split_and_conditions_for_case(condition: str) -> List[str]:
    """
    分割CASE语句中的AND/OR条件,每个AND/OR单独一行
    
    Args:
        condition: 条件文本
        
    Returns:
        条件行列表
    """
    lines = []
    separators = []  # 记录分隔符类型：'and'或'or'
    current = ''
    depth = 0
    i = 0
    
    while i < len(condition):
        char = condition[i]
        
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif depth == 0:
            # 检查AND或OR
            if condition[i:i+5].upper() == ' AND ':
                # 找到AND,保存当前行
                if current.strip():
                    lines.append(current.strip())
                    separators.append('and')
                current = ''
                i += 5
                continue
            elif condition[i:i+4].upper() == ' OR ':
                # 找到OR,保存当前行
                if current.strip():
                    lines.append(current.strip())
                    separators.append('or')
                current = ''
                i += 4
                continue
            else:
                current += char
        else:
            current += char
        
        i += 1
    
    if current.strip():
        lines.append(current.strip())
    
    # 如果只有一行,直接返回
    if len(lines) <= 1:
        return lines
    
    # 多行时,第二行开始加上对应的分隔符前缀
    result = [lines[0]]
    for i, line in enumerate(lines[1:]):
        sep = separators[i] if i < len(separators) else 'and'
        result.append(f'{sep} {line}')
    
    return result


def format_parenthesized_or_condition(condition: str) -> str:
    """
    格式化括号内的OR条件
    例如: (a = 1 or b = 2) -> (\n    a = 1\n    or b = 2\n  )
    也处理: and (a = 1 or b = 2) -> and (\n    a = 1\n    or b = 2\n  )
    
    Args:
        condition: 条件文本
        
    Returns:
        格式化后的条件
    """
    condition = condition.strip()
    
    # 检查是否以'and '开头
    and_prefix = ''
    if condition.lower().startswith('and '):
        and_prefix = 'and '
        condition = condition[4:].strip()
    
    # 检查是否是括号包裹的条件
    if not (condition.startswith('(') and condition.endswith(')')):
        return (and_prefix + condition) if and_prefix else condition
    
    # 提取括号内的内容
    inner = condition[1:-1].strip()
    
    # 检查是否包含OR（在括号深度为0时）
    has_or = False
    depth = 0
    i = 0
    while i < len(inner):
        if inner[i] == '(':
            depth += 1
        elif inner[i] == ')':
            depth -= 1
        elif depth == 0 and inner[i:i+4].upper() == ' OR ':
            has_or = True
            break
        i += 1
    
    if not has_or:
        return (and_prefix + condition) if and_prefix else condition
    
    # 分割OR条件
    or_parts = []
    current = ''
    depth = 0
    i = 0
    
    while i < len(inner):
        char = inner[i]
        
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif depth == 0 and inner[i:i+4].upper() == ' OR ':
            # 找到OR,保存当前部分
            if current.strip():
                or_parts.append(current.strip())
            current = ''
            i += 4
            continue
        else:
            current += char
        
        i += 1
    
    if current.strip():
        or_parts.append(current.strip())
    
    # 构建格式化的结果
    if len(or_parts) <= 1:
        return (and_prefix + condition) if and_prefix else condition
    
    # 格式化为多行 - 括号内容缩进2个空格（相对于and的位置）
    result = and_prefix + '(\n'
    result += '  ' + or_parts[0] + '\n'
    for part in or_parts[1:]:
        result += '  or ' + part + '\n'
    result += ')'
    
    return result


def format_json_object(expr: str, indent_level: int = 1) -> str:
    """
    格式化JSON_OBJECT函数
    
    Args:
        expr: JSON_OBJECT表达式
        indent_level: 缩进级别（用于内容的缩进）
        
    Returns:
        格式化后的表达式，包含完整的绝对缩进
    """
    # 计算基础缩进和内容缩进
    base_indent = '  ' * indent_level
    item_indent = '  ' * (indent_level + 1)
    
    # 找到JSON_OBJECT的起始位置
    json_start = expr.upper().find('JSON_OBJECT')
    if json_start < 0:
        return expr
    
    # 提取JSON_OBJECT部分
    json_expr = expr[json_start:]
    
    # 手动提取参数，考虑括号深度
    params_start = json_expr.find('(') + 1
    params_end = -1
    depth = 1
    in_string = False
    string_char = ''
    
    for i in range(params_start, len(json_expr)):
        char = json_expr[i]
        
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
        elif not in_string:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    params_end = i
                    break
    
    if params_end == -1:
        return expr
    
    # 提取参数部分
    params_part = json_expr[params_start:params_end].strip()
    if not params_part:
        return base_indent + 'JSON_OBJECT()'
    
    # 提取别名部分（保持原样，不添加AS）
    alias_part = json_expr[params_end+1:].strip()
    
    # 分割参数 - 按逗号分割，但要考虑字符串内的逗号
    params = []
    current_param = ''
    depth = 0
    in_string = False
    string_char = ''
    
    for char in params_part:
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
        elif not in_string:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                params.append(current_param.strip())
                current_param = ''
                continue
        
        current_param += char
    
    if current_param.strip():
        params.append(current_param.strip())
    
    # 构建格式化的JSON_OBJECT - 使用绝对缩进
    result_lines = [base_indent + 'JSON_OBJECT(']
    
    # 导入工具函数
    from .utils import separate_keywords, remove_space_before_paren
    
    # 成对处理参数 (key, value) - 每个参数对单独一行
    i = 0
    while i < len(params):
        key = params[i].strip()
        value = params[i+1].strip() if i+1 < len(params) else ''
        
        # 对value进行关键字分离处理
        value = separate_keywords(value)
        # 移除函数括号前后的空格
        value = remove_space_before_paren(value)
        
        # 确保key和value之间有逗号
        line = f'{item_indent}{key}, {value}'
        
        # 如果不是最后一对参数，添加逗号
        if i + 2 < len(params):
            line += ','
        
        result_lines.append(line)
        i += 2
    
    result_lines.append(f'{base_indent}){alias_part}')
    
    return '\n'.join(result_lines)


def format_from_clause(from_text: str, indent_level: int = 0) -> List[str]:
    """
    格式化FROM子句，特别处理JSON_TABLE、子查询和JOIN
    
    Args:
        from_text: FROM子句内容
        indent_level: 缩进级别（用于子查询）
        
    Returns:
        格式化后的行列表
    """
    base_indent = '  ' * indent_level
    result_lines = []
    
    # 首先检查是否包含JOIN（在括号深度为0时）
    join_keywords = ['FULL OUTER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'FULL JOIN', 'OUTER JOIN', 'JOIN']
    
    # 找到所有JOIN关键字的位置（考虑括号深度）
    join_positions = []
    depth = 0
    i = 0
    while i < len(from_text):
        if from_text[i] == '(':
            depth += 1
            i += 1
        elif from_text[i] == ')':
            depth -= 1
            i += 1
        elif depth == 0:
            # 检查是否是JOIN关键字（按长度从长到短检查）
            matched = False
            for kw in join_keywords:
                if from_text[i:i+len(kw)].upper() == kw:
                    # 确保是完整的单词（前后是空格或开头/结尾）
                    before_ok = (i == 0 or from_text[i-1].isspace())
                    after_ok = (i + len(kw) >= len(from_text) or from_text[i+len(kw)].isspace())
                    if before_ok and after_ok:
                        join_positions.append((i, kw))
                        i += len(kw)  # 跳过这个关键字
                        matched = True
                        break
            if not matched:
                i += 1
        else:
            i += 1
    
    # 如果找到JOIN，分离FROM部分和所有JOIN部分
    if join_positions:
        # 第一个JOIN之前是FROM部分
        from_part = from_text[:join_positions[0][0]].strip()
        
        # 格式化FROM部分（递归调用，不包含JOIN）
        from_lines = format_from_clause_no_join(from_part, indent_level)
        result_lines.extend(from_lines)
        
        # 处理每个JOIN
        for idx, (pos, kw) in enumerate(join_positions):
            # 确定这个JOIN的结束位置（下一个JOIN的开始位置或字符串结尾）
            if idx + 1 < len(join_positions):
                end_pos = join_positions[idx + 1][0]
            else:
                end_pos = len(from_text)
            
            join_part = from_text[pos:end_pos].strip()
            
            # 特殊处理FULL OUTER JOIN：FULL附加到最后一行，OUTER JOIN单独一行
            if kw == 'FULL OUTER JOIN':
                # 将FULL附加到最后一行
                if result_lines:
                    result_lines[-1] += ' FULL'
                
                # 格式化OUTER JOIN部分（去掉FULL）
                join_part_without_full = join_part[5:].strip()  # 去掉"FULL "
                join_lines = format_join_clause(join_part_without_full, indent_level)
                result_lines.extend(join_lines)
            else:
                # 格式化JOIN部分
                join_lines = format_join_clause(join_part, indent_level)
                result_lines.extend(join_lines)
        
        return result_lines
    
    # 没有JOIN，使用原有的处理逻辑
    return format_from_clause_no_join(from_text, indent_level)


def format_from_clause_no_join(from_text: str, indent_level: int = 0) -> List[str]:
    """
    格式化FROM子句（不包含JOIN），特别处理JSON_TABLE和子查询
    
    Args:
        from_text: FROM子句内容（不包含JOIN）
        indent_level: 缩进级别（用于子查询）
        
    Returns:
        格式化后的行列表
    """
    base_indent = '  ' * indent_level
    result_lines = []
    
    # 检查是否包含子查询(以括号开头)
    from_text_stripped = from_text.strip()
    if from_text_stripped.startswith('(') and 'SELECT' in from_text_stripped.upper():
        # 这是一个子查询
        # 找到匹配的右括号
        depth = 0
        i = 0
        for i, char in enumerate(from_text_stripped):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    break
        
        # 提取子查询内容(不包括外层括号)
        subquery_content = from_text_stripped[1:i].strip()
        # 提取别名(如果有)
        alias = from_text_stripped[i+1:].strip()
        
        # 检查子查询中是否包含UNION ALL
        # 需要检查在括号深度为0时是否有UNION ALL
        has_union_all = False
        depth_check = 0
        j = 0
        while j < len(subquery_content):
            if subquery_content[j] == '(':
                depth_check += 1
            elif subquery_content[j] == ')':
                depth_check -= 1
            elif depth_check == 0:
                # 检查是否是UNION ALL
                remaining = subquery_content[j:].upper()
                if remaining.startswith('UNION') and 'ALL' in remaining[:15]:
                    has_union_all = True
                    break
            j += 1
        
        # 根据是否包含UNION ALL选择不同的格式化函数
        if has_union_all:
            from .formatters import format_union_query
            formatted_subquery = format_union_query(subquery_content, indent_level=indent_level + 1)
            # 移除末尾的分号
            if formatted_subquery.endswith(';'):
                formatted_subquery = formatted_subquery[:-1]
        else:
            from .formatters import format_select
            # 子查询使用indent_level + 1，因为它在括号内部，比FROM子句深一层
            formatted_subquery = format_select(subquery_content, indent_level=indent_level + 1)
        
        # 构建结果:左括号单独一行,子查询内容,右括号和别名单独一行
        result_lines.append(base_indent + '  (')
        # 添加格式化的子查询
        # 子查询已经有了indent_level+1的缩进，我们需要再加上2个空格（括号内的缩进）
        for line in formatted_subquery.split('\n'):
            result_lines.append('  ' + line)
        result_lines.append(base_indent + '  ) ' + alias if alias else base_indent + '  )')
        
        return result_lines
    
    # 检查是否包含JSON_TABLE
    if 'JSON_TABLE' not in from_text.upper():
        # 没有JSON_TABLE，直接返回
        result_lines.append(base_indent + '  ' + from_text)
        return result_lines
    
    # 分割表和JSON_TABLE（按逗号分割，但要考虑括号）
    parts = []
    current = ''
    depth = 0
    
    for char in from_text:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            parts.append(current.strip())
            current = ''
            continue
        current += char
    
    if current.strip():
        parts.append(current.strip())
    
    # 格式化每个部分
    for i, part in enumerate(parts):
        if 'JSON_TABLE' in part.upper():
            # 格式化JSON_TABLE
            formatted_json_table = format_json_table_in_from(part)
            # 添加所有行（添加基础缩进）
            for line in formatted_json_table:
                result_lines.append(base_indent + line)
        else:
            # 普通表
            if i < len(parts) - 1:
                result_lines.append(base_indent + '  ' + part + ',')
            else:
                result_lines.append(base_indent + '  ' + part)
    
    return result_lines


def format_join_clause(join_text: str, indent_level: int = 0) -> List[str]:
    """
    格式化JOIN子句
    
    Args:
        join_text: JOIN子句文本（如 "LEFT JOIN t2 ON t1.id = t2.id and t2.status = 'active'"）
        indent_level: 缩进级别（用于子查询）
        
    Returns:
        格式化后的行列表
    """
    base_indent = '  ' * indent_level
    result_lines = []
    
    # 提取JOIN类型
    join_type_match = re.match(r'((?:LEFT|RIGHT|INNER|OUTER)?\s*JOIN)\s+', join_text, re.IGNORECASE)
    if not join_type_match:
        result_lines.append(base_indent + '  ' + join_text)
        return result_lines
    
    join_type = join_type_match.group(1).strip()
    rest = join_text[join_type_match.end():].strip()
    
    # 检查是否是子查询（以括号开头）
    if rest.startswith('('):
        # 找到匹配的右括号
        depth = 0
        i = 0
        for i, char in enumerate(rest):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    break
        
        # 提取子查询内容（不包括外层括号）
        subquery_content = rest[1:i].strip()
        # 提取别名和ON条件
        after_subquery = rest[i+1:].strip()
        
        # 查找ON关键字
        on_match = re.search(r'\s+ON\s+', after_subquery, re.IGNORECASE)
        if on_match:
            alias = after_subquery[:on_match.start()].strip()
            conditions = after_subquery[on_match.end():].strip()
        else:
            alias = after_subquery
            conditions = ''
        
        # 格式化子查询
        from .formatters import format_select
        # JOIN子查询使用与FROM子查询相同的模式：
        # 1. 调用format_select时使用indent_level + 1
        # 2. 添加行时加上'  '前缀，使最终缩进为indent_level + 2
        formatted_subquery = format_select(subquery_content, indent_level=indent_level + 1)
        
        # 构建结果
        result_lines.append(base_indent + '  ' + join_type + ' (')
        # 添加格式化的子查询
        # 子查询已经有了indent_level+1的缩进，我们需要再加上2个空格（括号内的缩进）
        for line in formatted_subquery.split('\n'):
            result_lines.append('  ' + line)
        
        # 处理ON条件
        if conditions:
            from .parser import split_and_conditions
            from .utils import add_space_around_equals, remove_space_before_paren
            condition_parts = split_and_conditions(conditions)
            
            # 如果只有一个条件，将别名和ON条件放在同一行
            if len(condition_parts) == 1:
                first_cond = condition_parts[0]
                first_cond = add_space_around_equals(first_cond)
                first_cond = remove_space_before_paren(first_cond)
                result_lines.append(base_indent + '  ) ' + alias + ' ON ' + first_cond if alias else base_indent + '  ) ON ' + first_cond)
            else:
                # 多个条件，别名单独一行
                result_lines.append(base_indent + '  ) ' + alias if alias else base_indent + '  )')
                
                # 第一个条件
                first_cond = condition_parts[0]
                first_cond = add_space_around_equals(first_cond)
                first_cond = remove_space_before_paren(first_cond)
                result_lines.append(base_indent + '  ON ' + first_cond)
                
                # 其余条件
                for cond in condition_parts[1:]:
                    cond = add_space_around_equals(cond)
                    cond = remove_space_before_paren(cond)
                    result_lines.append(base_indent + '  and ' + cond)
        else:
            result_lines.append(base_indent + '  ) ' + alias if alias else base_indent + '  )')
        
        return result_lines
    
    # 不是子查询，使用原有的处理逻辑
    # 匹配: table_name ON conditions
    match = re.match(r'(.+?)\s+ON\s+(.+)', rest, re.IGNORECASE | re.DOTALL)
    
    if not match:
        # 无法解析，直接返回
        result_lines.append(base_indent + '  ' + join_text)
        return result_lines
    
    table_part = match.group(1).strip()
    conditions = match.group(2).strip()
    
    # 分割ON条件（按and分割，考虑括号深度）
    from .parser import split_and_conditions
    from .utils import add_space_around_equals, remove_space_before_paren
    condition_parts = split_and_conditions(conditions)
    
    # 处理第一个条件：确保等号周围有空格，移除函数括号空格
    first_cond = condition_parts[0]
    first_cond = add_space_around_equals(first_cond)
    first_cond = remove_space_before_paren(first_cond)
    
    # JOIN类型和表名在同一行，ON和第一个条件也在同一行
    result_lines.append(base_indent + '  ' + join_type.upper() + ' ' + table_part + ' ON ' + first_cond)
    
    # 其余条件，每个单独一行
    for cond in condition_parts[1:]:
        cond = add_space_around_equals(cond)
        cond = remove_space_before_paren(cond)
        result_lines.append(base_indent + '  and ' + cond)
    
    return result_lines


def format_json_table_in_from(json_table_text: str) -> List[str]:
    """
    格式化FROM子句中的JSON_TABLE
    
    Args:
        json_table_text: JSON_TABLE文本
        
    Returns:
        格式化后的行列表
    """
    # 解析JSON_TABLE结构
    # JSON_TABLE (tccq.collectors,'$[*]' COLUMNS (`code` VARCHAR (100) PATH '$.code',`status` INT PATH '$.status')) AS jt
    
    # 首先找到AS关键字的位置（从后往前找，避免匹配到COLUMNS中的AS）
    as_pos = json_table_text.upper().rfind(' AS ')
    if as_pos == -1:
        return ['  ' + json_table_text]
    
    # 提取别名
    alias = json_table_text[as_pos + 4:].strip()
    
    # 提取JSON_TABLE内容（去掉"JSON_TABLE ("和最后的") AS alias"）
    json_table_start = json_table_text.upper().find('JSON_TABLE')
    if json_table_start == -1:
        return ['  ' + json_table_text]
    
    # 找到JSON_TABLE后的第一个左括号
    paren_start = json_table_text.find('(', json_table_start)
    if paren_start == -1:
        return ['  ' + json_table_text]
    
    # 找到匹配的右括号（考虑嵌套）
    depth = 1
    i = paren_start + 1
    while i < len(json_table_text) and depth > 0:
        if json_table_text[i] == '(':
            depth += 1
        elif json_table_text[i] == ')':
            depth -= 1
        i += 1
    
    if depth != 0:
        return ['  ' + json_table_text]
    
    # 提取JSON_TABLE的内容（不包括外层括号）
    content = json_table_text[paren_start + 1:i - 1].strip()
    
    # 找到COLUMNS的位置
    columns_pos = content.upper().find('COLUMNS')
    if columns_pos == -1:
        return ['  ' + json_table_text]
    
    # 分离参数和COLUMNS部分
    params_part = content[:columns_pos].strip()
    # 移除末尾的逗号（如果有）
    if params_part.endswith(','):
        params_part = params_part[:-1].strip()
    
    # 分割参数（按逗号分割，但要考虑括号和字符串）
    params = []
    current_param = ''
    depth = 0
    in_string = False
    string_char = None
    
    for char in params_part:
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
        elif not in_string:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                params.append(current_param.strip())
                current_param = ''
                continue
        
        current_param += char
    
    if current_param.strip():
        params.append(current_param.strip())
    
    # 提取COLUMNS内的内容
    columns_part = content[columns_pos:]
    columns_match = re.match(r'COLUMNS\s*\((.*)\)', columns_part, re.IGNORECASE | re.DOTALL)
    if not columns_match:
        return ['  ' + json_table_text]
    
    columns_content = columns_match.group(1).strip()
    
    # 分割列定义
    column_defs = []
    current_col = ''
    depth = 0
    
    for char in columns_content:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            column_defs.append(current_col.strip())
            current_col = ''
            continue
        current_col += char
    
    if current_col.strip():
        column_defs.append(current_col.strip())
    
    # 构建格式化的JSON_TABLE
    result = ['  JSON_TABLE (']
    
    # 添加参数
    for i, param in enumerate(params):
        if i < len(params) - 1:
            result.append('    ' + param + ',')
        else:
            result.append('    ' + param + ',')
    
    # 添加COLUMNS关键字
    result.append('    COLUMNS (')
    
    # 添加列定义
    for i, col_def in enumerate(column_defs):
        if i < len(column_defs) - 1:
            result.append('      ' + col_def + ',')
        else:
            result.append('      ' + col_def)
    
    result.append('    )')
    result.append('  ) AS ' + alias)
    
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
    result_lines = []
    
    for idx, (cte_name, cte_content) in enumerate(ctes):
        # 避免循环导入
        from .formatters import format_select
        # 格式化 SELECT 语句（缩进级别为 0，我们手动添加缩进）
        formatted_select = format_select(cte_content, indent_level=0)
        
        # 给SELECT的每一行添加2个空格的缩进
        select_lines = formatted_select.split('\n')
        indented_select_lines = ['  ' + line for line in select_lines]
        
        if idx == 0:
            result_lines.append(f'WITH {cte_name} AS(')
        else:
            # 逗号在右括号后，没有空格，然后换行
            result_lines[-1] += ','
            result_lines.append(f'{cte_name} AS(')
        
        # 添加格式化的 SELECT（已经有缩进）
        result_lines.extend(indented_select_lines)
        result_lines.append(')')
    
    # 添加最终的 SELECT
    if final_select:
        from .formatters import format_select
        formatted_final_select = format_select(final_select, indent_level=0)
        result_lines.append(formatted_final_select)
    
    return '\n'.join(result_lines)


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
        from .ddl_formatters import format_create_table
        return format_create_table(statement)
    
    create_part = match.group(1)
    with_part = match.group(2)
    
    # 格式化 WITH 子句
    formatted_with = format_with_clause(with_part)
    
    # 构建结果 - CREATE TABLE AS WITH 在同一行，末尾添加分号
    result = f'{create_part} AS {formatted_with};'
    
    return result



def format_nested_parentheses_condition(condition: str, base_indent: str = '  ') -> List[str]:
    """
    格式化嵌套括号条件
    例如: ((a = 1 and b = 2) or c = 3) -> 
      (
        (
          a = 1
          and b = 2
        )
        or c = 3
      )
    
    Args:
        condition: 条件文本
        base_indent: 基础缩进
        
    Returns:
        格式化后的行列表
    """
    condition = condition.strip()
    
    # 检查是否以括号开头和结尾
    if not (condition.startswith('(') and condition.endswith(')')):
        return [base_indent + condition]
    
    # 提取括号内的内容
    inner = condition[1:-1].strip()
    
    # 检查是否有嵌套括号（在深度为0时）
    has_nested = False
    depth = 0
    for char in inner:
        if char == '(':
            if depth == 0:
                has_nested = True
                break
            depth += 1
        elif char == ')':
            depth -= 1
    
    if not has_nested:
        # 没有嵌套括号，检查是否有OR/AND需要换行
        # 分割OR条件（优先级低）
        or_parts = []
        current = ''
        depth = 0
        i = 0
        
        while i < len(inner):
            char = inner[i]
            
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif depth == 0 and inner[i:i+4].upper() == ' OR ':
                if current.strip():
                    or_parts.append(current.strip())
                current = ''
                i += 4
                continue
            else:
                current += char
            
            i += 1
        
        if current.strip():
            or_parts.append(current.strip())
        
        if len(or_parts) > 1:
            # 有OR，需要换行
            result = [base_indent + '(']
            for idx, part in enumerate(or_parts):
                # 分割AND条件
                and_parts = []
                current = ''
                depth = 0
                i = 0
                
                while i < len(part):
                    char = part[i]
                    
                    if char == '(':
                        depth += 1
                        current += char
                    elif char == ')':
                        depth -= 1
                        current += char
                    elif depth == 0 and part[i:i+5].upper() == ' AND ':
                        if current.strip():
                            and_parts.append(current.strip())
                        current = ''
                        i += 5
                        continue
                    else:
                        current += char
                    
                    i += 1
                
                if current.strip():
                    and_parts.append(current.strip())
                
                if len(and_parts) > 1:
                    # 有AND，需要换行
                    if idx == 0:
                        result.append(base_indent + '  ' + and_parts[0])
                    else:
                        result.append(base_indent + '  or ' + and_parts[0])
                    for and_part in and_parts[1:]:
                        result.append(base_indent + '  and ' + and_part)
                else:
                    if idx == 0:
                        result.append(base_indent + '  ' + part)
                    else:
                        result.append(base_indent + '  or ' + part)
            
            result.append(base_indent + ')')
            return result
        else:
            # 没有OR，检查AND
            and_parts = []
            current = ''
            depth = 0
            i = 0
            
            while i < len(inner):
                char = inner[i]
                
                if char == '(':
                    depth += 1
                    current += char
                elif char == ')':
                    depth -= 1
                    current += char
                elif depth == 0 and inner[i:i+5].upper() == ' AND ':
                    if current.strip():
                        and_parts.append(current.strip())
                    current = ''
                    i += 5
                    continue
                else:
                    current += char
                
                i += 1
            
            if current.strip():
                and_parts.append(current.strip())
            
            if len(and_parts) > 1:
                # 有AND，需要换行
                result = [base_indent + '(']
                result.append(base_indent + '  ' + and_parts[0])
                for and_part in and_parts[1:]:
                    result.append(base_indent + '  and ' + and_part)
                result.append(base_indent + ')')
                return result
            else:
                # 单个条件，不需要换行
                return [base_indent + condition]
    
    # 有嵌套括号，递归处理
    result = [base_indent + '(']
    
    # 分割OR条件（在深度为0时）
    or_parts = []
    current = ''
    depth = 0
    i = 0
    
    while i < len(inner):
        char = inner[i]
        
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif depth == 0 and inner[i:i+4].upper() == ' OR ':
            if current.strip():
                or_parts.append(current.strip())
            current = ''
            i += 4
            continue
        else:
            current += char
        
        i += 1
    
    if current.strip():
        or_parts.append(current.strip())
    
    for idx, part in enumerate(or_parts):
        part_stripped = part.strip()
        
        # 检查这个部分是否是括号包裹的
        if part_stripped.startswith('(') and part_stripped.endswith(')'):
            # 递归处理
            formatted_part = format_nested_parentheses_condition(part_stripped, base_indent + '  ')
            
            if idx == 0:
                result.extend(formatted_part)
            else:
                # 在第一行前面加上 or
                if formatted_part:
                    first_line = formatted_part[0]
                    # 移除基础缩进，添加or，再加回缩进
                    content = first_line.strip()
                    result.append(base_indent + '  or ' + content)
                    result.extend(formatted_part[1:])
        else:
            # 不是括号包裹的，检查是否有AND需要换行
            and_parts = []
            current = ''
            depth = 0
            i = 0
            
            while i < len(part):
                char = part[i]
                
                if char == '(':
                    depth += 1
                    current += char
                elif char == ')':
                    depth -= 1
                    current += char
                elif depth == 0 and part[i:i+5].upper() == ' AND ':
                    if current.strip():
                        and_parts.append(current.strip())
                    current = ''
                    i += 5
                    continue
                else:
                    current += char
                
                i += 1
            
            if current.strip():
                and_parts.append(current.strip())
            
            if len(and_parts) > 1:
                # 有AND，需要换行
                if idx == 0:
                    result.append(base_indent + '  ' + and_parts[0])
                else:
                    result.append(base_indent + '  or ' + and_parts[0])
                for and_part in and_parts[1:]:
                    result.append(base_indent + '  and ' + and_part)
            else:
                if idx == 0:
                    result.append(base_indent + '  ' + part)
                else:
                    result.append(base_indent + '  or ' + part)
    
    result.append(base_indent + ')')
    return result




def format_window_function(expr: str, indent_level: int) -> str:
    """
    格式化窗口函数
    
    Args:
        expr: 窗口函数表达式
        indent_level: 缩进级别
        
    Returns:
        格式化后的表达式
    """
    base_indent = '  ' * indent_level
    inner_indent = '  ' * (indent_level + 1)
    content_indent = '  ' * (indent_level + 2)
    
    # 查找 OVER( ... ) - 允许OVER和括号之间有空格（输入时），但输出时统一为无空格
    over_match = re.search(r'(.*?)\s*OVER\s*\((.*?)\)(\s+[Aa][Ss]\s+\w+)?$', expr, re.IGNORECASE | re.DOTALL)
    if not over_match:
        return expr
    
    func_part = over_match.group(1).strip()  # 函数部分，如 ROW_NUMBER()
    over_content = over_match.group(2).strip()  # OVER内的内容
    as_clause = over_match.group(3).strip() if over_match.group(3) else ''
    
    # 解析 OVER 内容 - 统一格式：OVER后无空格
    result_lines = [f'{base_indent}{func_part} OVER(']
    
    # 检查是否有 PARTITION BY
    partition_match = re.search(r'PARTITION\s+BY\s+(.*?)(?=ORDER\s+BY|$)', over_content, re.IGNORECASE | re.DOTALL)
    if partition_match:
        partition_cols = partition_match.group(1).strip()
        # 确保PARTITION BY在OVER后面单独成行
        result_lines.append(f'{inner_indent}PARTITION BY {partition_cols}')
    
    # 检查是否有 ORDER BY
    order_match = re.search(r'ORDER\s+BY\s+(.*)', over_content, re.IGNORECASE | re.DOTALL)
    if order_match:
        order_expr = order_match.group(1).strip()
        # 确保ORDER BY在PARTITION BY后面单独成行
        result_lines.append(f'{inner_indent}ORDER BY')
        result_lines.append(f'{content_indent}{order_expr}')
    
    # 确保AS子句前有空格
    if as_clause and not as_clause.startswith(' '):
        as_clause = ' ' + as_clause
    
    result_lines.append(f'{base_indent}){as_clause}')
    
    return '\n'.join(result_lines)