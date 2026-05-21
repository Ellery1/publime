"""
Doris 日志处理模块

解析 doris 日志中的 SQL 模板和参数，用参数值替换占位符 `?`，
并调用 format_sql 进行格式化，生成可直接执行的 SQL。

参考实现：samples/SqlFormatterUtil.java
"""

import re

from core.sql_formatter import format_sql


def extract_sql_from_log(line: str) -> str:
    """
    从 SQL 日志行中提取 SQL 模板。

    支持两种前缀：
    - 'Preparing:' (MyBatis 日志格式)
    - '执行sql:' (自定义日志格式)

    Args:
        line: 包含 SQL 的日志行

    Returns:
        提取出的 SQL 模板字符串

    Raises:
        ValueError: 日志行不包含任何已知前缀
    """
    if '执行sql:' in line:
        start = line.index('执行sql:') + len('执行sql:')
        return line[start:].strip()
    elif 'Preparing:' in line:
        start = line.index('Preparing:') + len('Preparing:')
        return line[start:].strip()
    raise ValueError("无法识别的SQL日志格式，必须包含'执行sql:'或'Preparing:'前缀")


def remove_count_wrapper(sql: str) -> str:
    """
    去除 SQL 外层的 COUNT 包裹。

    如果 SQL 以 'SELECT COUNT(1) as total FROM (' 开头且以 ') TMP' 结尾，
    则去除外层包裹，返回内部 SQL。否则原样返回。
    """
    prefix = 'SELECT COUNT(1) as total FROM ('
    suffix = ') TMP'

    if sql.startswith(prefix):
        sql = sql[len(prefix):]
    if sql.endswith(suffix):
        sql = sql[:len(sql) - len(suffix)]
    return sql.strip()


def extract_parameters_preparing(param_str: str) -> list[str]:
    """
    从 'Parameters:' 格式的参数字符串中提取参数值列表。

    格式: 'value1(Type), value2(Type), ...'
    使用负向前瞻正则 `,(?![^()]*\\))` 确保不分割括号内的逗号，
    然后用 `\\(.*\\)` 去除类型声明。
    """
    parts = re.split(r',(?![^()]*\))', param_str)
    return [re.sub(r'\(.*\)', '', p).strip() for p in parts]


def extract_parameters_exec(param_str: str) -> list[str]:
    """
    从 '执行参数:' 格式的参数字符串中提取参数值列表。

    格式: '["value1","value2",123]'
    先去除外层 []，然后用正则匹配带引号的字符串和不带引号的值。
    """
    param_str = re.sub(r'^\[|]$', '', param_str.strip())
    params = []
    for m in re.finditer(r'"([^"]*)"|([^,]+)', param_str):
        if m.group(1) is not None:
            params.append(m.group(1))
        elif m.group(2) is not None:
            params.append(m.group(2).strip())
    return params


def extract_parameters(line: str) -> list[str]:
    """
    从参数日志行中提取参数值列表。

    自动识别 'Parameters:' 或 '执行参数:' 格式并分派到对应的提取函数。

    Raises:
        ValueError: 无法识别的参数格式
    """
    if '执行参数:' in line:
        start = line.index('执行参数:') + len('执行参数:')
        return extract_parameters_exec(line[start:].strip())
    elif 'Parameters:' in line:
        start = line.index('Parameters:') + len('Parameters:')
        return extract_parameters_preparing(line[start:].strip())
    raise ValueError("无法识别的参数格式")


def is_datetime_param(param: str) -> bool:
    """判断参数是否为日期时间格式（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）"""
    return bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?', param))


def is_numeric(param: str) -> bool:
    """判断参数是否为数字格式（整数或小数，可带负号）"""
    return bool(re.fullmatch(r'-?\d+(\.\d+)?', param))


def replace_parameters(sql: str, params: list[str]) -> str:
    """
    将 SQL 模板中的 ? 占位符替换为实际参数值。

    替换规则（与 SqlFormatterUtil.java 一致）：
    - 先判断日期格式 → 用单引号包裹
    - 再判断数字格式 → 直接替换
    - 其余视为字符串 → 用单引号包裹

    Raises:
        ValueError: 参数数量与占位符数量不匹配
    """
    placeholder_count = sql.count('?')
    if placeholder_count != len(params):
        raise ValueError(
            f"参数个数不匹配。SQL需要{placeholder_count}个参数，但提供了{len(params)}个参数"
        )

    result = []
    param_index = 0
    last_pos = 0
    for m in re.finditer(r'\?', sql):
        result.append(sql[last_pos:m.start()])
        param = params[param_index]
        if is_datetime_param(param) or not is_numeric(param):
            result.append(f"'{param}'")
        else:
            result.append(param)
        param_index += 1
        last_pos = m.end()
    result.append(sql[last_pos:])
    return ''.join(result)


def process_doris_log(text: str) -> tuple[bool, str]:
    """
    处理 doris 日志文本，生成格式化后的 SQL。

    扫描所有行，按前缀分类：
    - '执行sql:' 或 'Preparing:' → SQL 起始行
    - '执行参数:' 或 'Parameters:' → 参数行
    - 其余行（在 SQL 起始行之后、参数行之前）→ SQL 续行

    支持 myBatis 两行格式和 doris-api 多行格式。

    Args:
        text: 编辑器中的完整文本

    Returns:
        (True, formatted_sql) 成功时返回格式化后的 SQL
        (False, error_message) 失败时返回错误信息
    """
    lines = text.strip().split('\n')

    sql_parts = []
    param_line = None
    sql_started = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if '执行参数:' in stripped or 'Parameters:' in stripped:
            param_line = stripped
            break

        if '执行sql:' in stripped or 'Preparing:' in stripped:
            sql_started = True
            raw = extract_sql_from_log(stripped)
            sql_parts.append(raw)
            continue

        if sql_started:
            sql_parts.append(stripped)

    if not sql_parts:
        return (False, "未找到SQL内容，请确认输入包含 '执行sql:' 或 'Preparing:'")
    if param_line is None:
        return (False, "未找到参数行，请确认输入包含 '执行参数:' 或 'Parameters:'")

    try:
        full_sql = ' '.join(sql_parts)
        processed_sql = remove_count_wrapper(full_sql)
        params = extract_parameters(param_line)

        executable_sql = replace_parameters(processed_sql, params)
        formatted_sql = format_sql(executable_sql)
        return (True, formatted_sql)
    except ValueError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"SQL处理异常: {str(e)}")
