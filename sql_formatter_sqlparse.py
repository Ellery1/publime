"""
使用 sqlparse 库的 SQL 格式化器

提供更强大的 SQL 格式化功能，支持：
- WITH (CTE) 子句
- 嵌套子查询
- CASE 语句
- 窗口函数
- ON DUPLICATE KEY UPDATE
等复杂 SQL 语法
"""

import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function, Where, Parenthesis
from sqlparse.tokens import Keyword, DML


def format_sql(sql_text: str) -> str:
    """
    格式化 SQL 文本
    
    Args:
        sql_text: 原始 SQL 文本
        
    Returns:
        格式化后的 SQL 文本
    """
    # 使用 sqlparse 格式化
    formatted = sqlparse.format(
        sql_text,
        reindent=True,              # 重新缩进
        indent_width=2,             # 缩进宽度为 2 个空格
        keyword_case='upper',       # 关键字大写
        identifier_case=None,       # 标识符保持原样
        strip_comments=False,       # 保留注释
        use_space_around_operators=True,  # 操作符周围使用空格
        indent_after_first=False,   # 第一个关键字不缩进
        indent_columns=False,       # 列不额外缩进
        wrap_after=0,               # 不自动换行
        comma_first=False,          # 逗号在行尾
    )
    
    # 清理多余的空行
    lines = formatted.split('\n')
    cleaned_lines = []
    prev_empty = False
    
    for line in lines:
        is_empty = not line.strip()
        
        # 跳过连续的空行
        if is_empty and prev_empty:
            continue
        
        cleaned_lines.append(line)
        prev_empty = is_empty
    
    result = '\n'.join(cleaned_lines)
    
    # 确保以分号结尾的语句后有空行
    result = result.replace(';\n', ';\n\n')
    
    # 清理多余的空行（再次）
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')
    
    return result.strip()


def format_sql_custom(sql_text: str) -> str:
    """
    自定义格式化（如果需要更精细的控制）
    
    Args:
        sql_text: 原始 SQL 文本
        
    Returns:
        格式化后的 SQL 文本
    """
    # 解析 SQL
    parsed = sqlparse.parse(sql_text)
    
    formatted_statements = []
    
    for statement in parsed:
        # 格式化每条语句
        formatted = sqlparse.format(
            str(statement),
            reindent=True,
            indent_width=2,
            keyword_case='upper',
            identifier_case=None,
            strip_comments=False,
            use_space_around_operators=True,
        )
        formatted_statements.append(formatted.strip())
    
    # 合并所有语句
    result = '\n\n'.join(formatted_statements)
    
    return result


if __name__ == '__main__':
    # 测试
    test_sql = """
    -- 测试 SQL
    CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(50));
    
    INSERT INTO employees (id, name) VALUES (1, 'John'), (2, 'Jane');
    
    SELECT * FROM employees WHERE id = 1;
    
    UPDATE employees SET name = 'John Doe' WHERE id = 1;
    
    DELETE FROM employees WHERE id = 1;
    
    /* 复杂查询 */
    WITH customer_stats AS (
        SELECT user_id, COUNT(*) as order_count
        FROM orders
        WHERE status != 'cancelled'
        GROUP BY user_id
    )
    SELECT cs.*, u.username
    FROM customer_stats cs
    JOIN users u ON cs.user_id = u.user_id
    WHERE order_count > 5;
    """
    
    print("=" * 80)
    print("SQL 格式化测试")
    print("=" * 80)
    print("\n原始 SQL:")
    print(test_sql)
    print("\n" + "=" * 80)
    print("格式化后:")
    print("=" * 80)
    print(format_sql(test_sql))
