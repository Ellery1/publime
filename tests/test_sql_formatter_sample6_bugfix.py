"""
Bug条件探索性测试——Sample 6 六类格式化缺陷

此测试在未修复代码上运行，预期FAIL——失败即证明bug存在。
不要修复代码或测试。

修复后重新运行，PASS即证明bug已修复。

Validates: Requirements 1.1, 1.2, 1.3, 1.5, 1.6
"""

import os
import pytest
from core.sql_formatter import format_sql


class TestBug1SumCaseExpression:
    """
    Bug 1: SUM(CASE WHEN ... END) 未正确展开为多行。

    期望：SUM ( 后换行，CASE/WHEN/ELSE/END正确缩进，) 与SUM对齐。

    Validates: Requirements 1.1
    """

    def test_sum_case_multiline_expansion(self):
        sql = (
            "SELECT SUM (CASE WHEN col IN ('0', '3') "
            "THEN amount ELSE 0 END) AS total FROM t"
        )
        result = format_sql(sql)

        # SUM ( 应该单独出现在一行末尾（缩进后）
        assert "SUM (" in result, (
            f"期望输出包含 'SUM ('，实际输出：\n{result}"
        )

        lines = result.splitlines()
        # 找到包含 "SUM (" 的行
        sum_lines = [i for i, l in enumerate(lines) if "SUM (" in l]
        assert len(sum_lines) >= 1, f"未找到包含 'SUM (' 的行，输出：\n{result}"

        sum_line_idx = sum_lines[0]
        sum_line = lines[sum_line_idx]

        # SUM ( 后面不应该紧跟 CASE（应该换行）
        assert sum_line.strip() == "SUM (", (
            f"期望 'SUM (' 单独一行，实际该行为：{repr(sum_line.strip())}，"
            f"完整输出：\n{result}"
        )

        # 后续行应包含正确缩进的 CASE/WHEN/ELSE/END
        remaining = "\n".join(lines[sum_line_idx + 1:])
        assert "CASE" in remaining, f"SUM(后未找到CASE，输出：\n{result}"
        assert "WHEN" in remaining, f"SUM(后未找到WHEN，输出：\n{result}"
        assert "ELSE 0" in remaining, f"SUM(后未找到ELSE，输出：\n{result}"
        assert "END" in remaining, f"SUM(后未找到END，输出：\n{result}"

        # ) 应该与 SUM 对齐（相同缩进级别）
        sum_indent = len(sum_line) - len(sum_line.lstrip())
        # 找到 SUM( 之后的闭合 )
        close_paren_lines = [
            i for i in range(sum_line_idx + 1, len(lines))
            if lines[i].strip().startswith(") AS") or lines[i].strip() == ")"
        ]
        assert len(close_paren_lines) >= 1, (
            f"未找到与SUM对齐的闭合括号行，输出：\n{result}"
        )
        close_line = lines[close_paren_lines[0]]
        close_indent = len(close_line) - len(close_line.lstrip())
        assert close_indent == sum_indent, (
            f"闭合括号缩进({close_indent})与SUM缩进({sum_indent})不一致，"
            f"输出：\n{result}"
        )


class TestBug2CountDistinctCaseExpression:
    """
    Bug 2: COUNT(DISTINCT(CASE WHEN ... END)) 未正确展开为多行。

    期望：COUNT ( 后换行，DISTINCT ( 缩进一行，CASE在内部缩进。

    Validates: Requirements 1.2
    """

    def test_count_distinct_case_multiline_expansion(self):
        sql = (
            "SELECT COUNT (DISTINCT (CASE WHEN col IN ('0', '3') "
            "THEN id END)) AS cnt FROM t"
        )
        result = format_sql(sql)

        lines = result.splitlines()

        # COUNT ( 应该单独一行
        count_lines = [i for i, l in enumerate(lines) if "COUNT (" in l]
        assert len(count_lines) >= 1, (
            f"未找到包含 'COUNT (' 的行，输出：\n{result}"
        )
        count_line_idx = count_lines[0]
        count_line = lines[count_line_idx]
        assert count_line.strip() == "COUNT (", (
            f"期望 'COUNT (' 单独一行，实际该行为：{repr(count_line.strip())}，"
            f"完整输出：\n{result}"
        )

        # DISTINCT ( 应该在下一行，缩进更深
        remaining_lines = lines[count_line_idx + 1:]
        distinct_lines = [
            i for i, l in enumerate(remaining_lines)
            if "DISTINCT (" in l
        ]
        assert len(distinct_lines) >= 1, (
            f"COUNT(后未找到 'DISTINCT (' 行，输出：\n{result}"
        )
        distinct_line = remaining_lines[distinct_lines[0]]
        assert distinct_line.strip() == "DISTINCT (", (
            f"期望 'DISTINCT (' 单独一行，实际该行为：{repr(distinct_line.strip())}，"
            f"完整输出：\n{result}"
        )

        # CASE 应该在 DISTINCT 之后出现
        remaining_after_distinct = "\n".join(
            remaining_lines[distinct_lines[0] + 1:]
        )
        assert "CASE" in remaining_after_distinct, (
            f"DISTINCT(后未找到CASE，输出：\n{result}"
        )


class TestBug3CastSubstringIfNesting:
    """
    Bug 3: CAST(SUBSTRING(if(...))) 深层嵌套函数未正确展开。

    期望：if参数展开为多行。

    Validates: Requirements 1.3
    """

    def test_cast_substring_if_multiline(self):
        sql = (
            "SELECT CAST (SUBSTRING (if (type='person', id1, id2)"
            ", 17, 1) AS UNSIGNED) % 2 AS gender FROM t"
        )
        result = format_sql(sql)

        lines = result.splitlines()

        # if 函数的参数应该展开为多行
        # 查找包含 "if (" 的行
        if_lines = [i for i, l in enumerate(lines) if "if (" in l.lower()]
        assert len(if_lines) >= 1, (
            f"未找到包含 'if (' 的行，输出：\n{result}"
        )

        # if 的三个参数不应该全在同一行
        if_line = lines[if_lines[0]]
        # 如果 if 的所有参数都在同一行，说明没有展开
        if_content = if_line.strip()
        # 检查 if 后面的内容是否跨多行
        # 期望 if ( 后面换行，参数分行显示
        has_multiline_if = False
        for i in range(if_lines[0], min(if_lines[0] + 5, len(lines))):
            line = lines[i].strip()
            if any(
                kw in line
                for kw in ["up.national_id", "up2.national_id", "id1", "id2"]
            ):
                # 参数出现在不同行说明已展开
                if i != if_lines[0]:
                    has_multiline_if = True
                    break

        assert has_multiline_if, (
            f"期望if函数参数展开为多行，但参数似乎都在同一行，"
            f"输出：\n{result}"
        )


class TestBug5NotEqualOperatorSpacing:
    """
    Bug 5: != 运算符两侧缺少空格。

    期望：!= 两侧各有一个空格。

    Validates: Requirements 1.5
    """

    def test_not_equal_operator_spacing(self):
        sql = (
            "SELECT 1 FROM t "
            "WHERE op_flag!='DELETE' AND status!='CLOSED'"
        )
        result = format_sql(sql)

        # != 两侧应各有一个空格
        assert "op_flag != 'DELETE'" in result, (
            f"期望输出包含 \"op_flag != 'DELETE'\"（!=两侧各一个空格），"
            f"实际输出：\n{result}"
        )
        assert "status != 'CLOSED'" in result, (
            f"期望输出包含 \"status != 'CLOSED'\"（!=两侧各一个空格），"
            f"实际输出：\n{result}"
        )


class TestBug6HavingClause:
    """
    Bug 6: HAVING子句未正确格式化。

    期望：HAVING单独一行，条件按AND分行并缩进。

    Validates: Requirements 1.6
    """

    def test_having_clause_formatting(self):
        sql = (
            "SELECT col, SUM (amount) FROM t "
            "GROUP BY col "
            "HAVING SUM (amount) >= 1.00 AND SUM (amount) <= 100.00"
        )
        result = format_sql(sql)

        lines = result.splitlines()

        # HAVING 应该单独一行
        having_lines = [
            i for i, l in enumerate(lines)
            if l.strip() == "HAVING"
        ]
        assert len(having_lines) >= 1, (
            f"期望 'HAVING' 单独一行，未找到。输出：\n{result}"
        )

        having_idx = having_lines[0]

        # HAVING 后面的条件应该缩进2空格
        if having_idx + 1 < len(lines):
            first_cond = lines[having_idx + 1]
            assert "SUM" in first_cond and ">=" in first_cond, (
                f"HAVING后第一行应包含第一个条件（SUM...>=...），"
                f"实际为：{repr(first_cond)}，输出：\n{result}"
            )
            # 检查缩进
            having_indent = len(lines[having_idx]) - len(
                lines[having_idx].lstrip()
            )
            cond_indent = len(first_cond) - len(first_cond.lstrip())
            assert cond_indent == having_indent + 2, (
                f"条件缩进({cond_indent})应为HAVING缩进({having_indent})+2，"
                f"输出：\n{result}"
            )

        # AND 条件应该在下一行
        if having_idx + 2 < len(lines):
            second_cond = lines[having_idx + 2]
            assert "AND" in second_cond and "SUM" in second_cond, (
                f"HAVING后第二行应包含AND条件，"
                f"实际为：{repr(second_cond)}，输出：\n{result}"
            )


class TestSample6FullComparison:
    """
    完整sample_6测试：格式化sample_6.sql，与sample_target_6.sql对比。

    注意target文件名是 sample_target_6.sql（不是 sample_6_target.sql）。

    Validates: Requirements 1.1, 1.2, 1.3, 1.5, 1.6
    """

    def test_sample_6_matches_target(self):
        samples_dir = os.path.join(os.path.dirname(__file__), "..", "samples")
        sql_path = os.path.join(samples_dir, "sample_6.sql")
        target_path = os.path.join(samples_dir, "sample_target_6.sql")

        with open(sql_path, encoding="utf-8") as f:
            sql = f.read()
        with open(target_path, encoding="utf-8") as f:
            expected = f.read()

        actual = format_sql(sql)

        if actual != expected:
            actual_lines = actual.splitlines()
            expected_lines = expected.splitlines()
            diffs = []
            max_len = max(len(actual_lines), len(expected_lines))
            for i in range(max_len):
                a = actual_lines[i] if i < len(actual_lines) else "<缺失>"
                e = expected_lines[i] if i < len(expected_lines) else "<缺失>"
                if a != e:
                    diffs.append((i + 1, a, e))

            diff_report = "\n".join(
                f"  第{lineno}行:\n    实际: {repr(a)}\n    期望: {repr(e)}"
                for lineno, a, e in diffs[:30]
            )
            pytest.fail(
                f"sample_6格式化结果与sample_target_6.sql不一致，"
                f"共{len(diffs)}行差异：\n{diff_report}"
            )
