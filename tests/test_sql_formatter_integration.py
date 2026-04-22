"""
集成测试——sample_5和sample_6完整对比

格式化sample_5.sql和sample_6.sql，与对应target文件逐字符对比，确认完全一致。

Validates: Requirements 2.1, 2.2, 2.3, 2.4
"""

import os
import pytest
from core.sql_formatter import format_sql


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def get_diff_lines(actual: str, expected: str):
    """返回差异行列表，每项为 (行号, 实际内容, 期望内容)"""
    actual_lines = actual.splitlines()
    expected_lines = expected.splitlines()
    diffs = []
    max_len = max(len(actual_lines), len(expected_lines))
    for i in range(max_len):
        a = actual_lines[i] if i < len(actual_lines) else "<缺失>"
        e = expected_lines[i] if i < len(expected_lines) else "<缺失>"
        if a != e:
            diffs.append((i + 1, a, e))
    return diffs


class TestSample5Integration:
    """格式化sample_5.sql，与sample_5_target.sql逐字符对比"""

    def test_sample_5_matches_target(self):
        sql = read_file(os.path.join(SAMPLES_DIR, "sample_5.sql"))
        expected = read_file(os.path.join(SAMPLES_DIR, "sample_5_target.sql"))
        actual = format_sql(sql)

        diffs = get_diff_lines(actual, expected)
        if diffs:
            diff_report = "\n".join(
                f"  第{lineno}行:\n    实际: {repr(a)}\n    期望: {repr(e)}"
                for lineno, a, e in diffs[:20]  # 最多显示20行差异
            )
            pytest.fail(
                f"sample_5格式化结果与target不一致，共{len(diffs)}行差异：\n{diff_report}"
            )

        assert actual == expected


class TestSample6Integration:
    """格式化sample_6.sql，与sample_6_target.sql逐字符对比"""

    def test_sample_6_matches_target(self):
        sql = read_file(os.path.join(SAMPLES_DIR, "sample_6.sql"))
        expected = read_file(os.path.join(SAMPLES_DIR, "sample_target_6.sql"))
        actual = format_sql(sql)

        diffs = get_diff_lines(actual, expected)
        if diffs:
            diff_report = "\n".join(
                f"  第{lineno}行:\n    实际: {repr(a)}\n    期望: {repr(e)}"
                for lineno, a, e in diffs[:20]
            )
            pytest.fail(
                f"sample_6格式化结果与target不一致，共{len(diffs)}行差异：\n{diff_report}"
            )

        assert actual == expected
