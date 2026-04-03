"""
保留性属性测试（修复前运行，验证基线行为）

此测试在未修复代码上运行，预期全部 PASS。
修复后也必须继续 PASS（回归基线）。

Validates: Requirements 3.1, 3.2, 3.3, 3.4
"""

import os
import pytest
from core.sql_formatter import format_sql

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'samples')


def read_file(filename: str) -> str:
    path = os.path.join(SAMPLES_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


class TestPreservationBaseline:
    """
    Property 2: Preservation — sample_1~4 和 complex_test 格式化结果不变。

    对每个 SQL 文件，格式化输出与对应 target 文件逐字符完全一致。

    Validates: Requirements 3.1, 3.2
    """

    def test_complex_test_matches_target(self):
        """
        格式化 complex_test.sql，与 complex_test_target.sql 逐字符对比，断言完全一致。

        Validates: Requirements 3.1, 3.2
        """
        sql = read_file('complex_test.sql')
        expected = read_file('complex_test_target.sql')
        result = format_sql(sql)
        assert result == expected, (
            f"complex_test.sql 格式化结果与 target 不一致。\n"
            f"期望长度: {len(expected)}，实际长度: {len(result)}\n"
            f"首个差异位置: {_first_diff_pos(result, expected)}"
        )

    def test_sample_1_matches_target(self):
        """
        格式化 sample_1.sql，与 sample_1_target.sql 逐字符对比，断言完全一致。

        Validates: Requirements 3.1, 3.2
        """
        sql = read_file('sample_1.sql')
        expected = read_file('sample_1_target.sql')
        result = format_sql(sql)
        assert result == expected, (
            f"sample_1.sql 格式化结果与 target 不一致。\n"
            f"期望长度: {len(expected)}，实际长度: {len(result)}\n"
            f"首个差异位置: {_first_diff_pos(result, expected)}"
        )

    def test_sample_2_matches_target(self):
        """
        格式化 sample_2.sql，与 sample_2_target.sql 逐字符对比，断言完全一致。

        Validates: Requirements 3.1, 3.2
        """
        sql = read_file('sample_2.sql')
        expected = read_file('sample_2_target.sql')
        result = format_sql(sql)
        assert result == expected, (
            f"sample_2.sql 格式化结果与 target 不一致。\n"
            f"期望长度: {len(expected)}，实际长度: {len(result)}\n"
            f"首个差异位置: {_first_diff_pos(result, expected)}"
        )

    def test_sample_3_matches_target(self):
        """
        格式化 sample_3.sql，与 sample_3_target.sql 逐字符对比，断言完全一致。

        Validates: Requirements 3.1, 3.2
        """
        sql = read_file('sample_3.sql')
        expected = read_file('sample_3_target.sql')
        result = format_sql(sql)
        assert result == expected, (
            f"sample_3.sql 格式化结果与 target 不一致。\n"
            f"期望长度: {len(expected)}，实际长度: {len(result)}\n"
            f"首个差异位置: {_first_diff_pos(result, expected)}"
        )

    def test_sample_4_matches_target(self):
        """
        格式化 sample_4.sql，与 sample_4_target.sql 逐字符对比，断言完全一致。

        Validates: Requirements 3.1, 3.2
        """
        sql = read_file('sample_4.sql')
        expected = read_file('sample_4_target.sql')
        result = format_sql(sql)
        assert result == expected, (
            f"sample_4.sql 格式化结果与 target 不一致。\n"
            f"期望长度: {len(expected)}，实际长度: {len(result)}\n"
            f"首个差异位置: {_first_diff_pos(result, expected)}"
        )


def _first_diff_pos(actual: str, expected: str) -> str:
    """返回首个差异位置的描述信息，便于调试。"""
    min_len = min(len(actual), len(expected))
    for i in range(min_len):
        if actual[i] != expected[i]:
            # 找到所在行号
            line_num = actual[:i].count('\n') + 1
            col_num = i - actual[:i].rfind('\n')
            # 显示上下文
            start = max(0, i - 40)
            end = min(len(actual), i + 40)
            actual_ctx = repr(actual[start:end])
            exp_start = max(0, i - 40)
            exp_end = min(len(expected), i + 40)
            expected_ctx = repr(expected[exp_start:exp_end])
            return (
                f"字符位置 {i}（第 {line_num} 行，第 {col_num} 列）\n"
                f"  实际上下文:  {actual_ctx}\n"
                f"  期望上下文:  {expected_ctx}"
            )
    if len(actual) != len(expected):
        return f"内容相同但长度不同：实际 {len(actual)}，期望 {len(expected)}"
    return "无差异"
