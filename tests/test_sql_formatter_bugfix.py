"""
Bug条件探索性测试（修复前运行）

此测试在未修复代码上运行，预期FAIL——失败即证明bug存在。
不要修复代码或测试。

Validates: Requirements 1.1, 1.2, 1.3, 1.4
"""

import pytest
from core.sql_formatter import format_sql


class TestBug12OperatorSpacing:
    """
    Bug 1/2: 运算符空格——format_select普通列路径未调用add_space_around_equals，
    且remove_space_before_paren错误移除了if函数名与括号间的空格。

    根据design.md，Bug 1的期望输出是：
      if (tct.loan_status = 'SETTLE', '是', '否')
    当前输出是：
      if(tct.loan_status = 'SETTLE', '是', '否')  ← 函数名后空格被移除
    """

    def test_if_function_space_and_equals_operator(self):
        """
        格式化包含IF函数且等号两侧无空格的SELECT列，
        断言输出中：
          1. loan_status = 'SETTLE'（等号两侧各有一个空格）
          2. if (tct.loan_status（函数名与括号间保留空格）

        Validates: Requirements 1.1, 1.2
        """
        sql = "SELECT if ( tct.loan_status= 'SETTLE', '是', '否') FROM t"
        result = format_sql(sql)
        # 断言等号两侧各有一个空格，且函数名与括号间保留空格
        assert "if (tct.loan_status = 'SETTLE'" in result, (
            f"期望输出包含 \"if (tct.loan_status = 'SETTLE'\"（函数名后保留空格，等号两侧各一个空格），"
            f"实际输出：\n{result}"
        )


class TestBug3InClauseSpacing:
    """
    Bug 3: IN子句空格——format_in_clause正则(.*?)非贪婪匹配失败，
    导致括号内多余空格未被清理。
    """

    def test_in_clause_no_extra_spaces(self):
        """
        格式化IN子句括号内有多余空格的SQL，
        断言输出包含 in ('LOAN', 'REPAYMENT', 'SPECIAL')（括号内无多余空格）。

        Validates: Requirements 1.3
        """
        sql = "SELECT 1 FROM t WHERE col in ( 'LOAN' , 'REPAYMENT' , 'SPECIAL' )"
        result = format_sql(sql)
        # 断言括号内无多余空格，逗号后有且仅有一个空格
        assert "in ('LOAN', 'REPAYMENT', 'SPECIAL')" in result, (
            f"期望输出包含 \"in ('LOAN', 'REPAYMENT', 'SPECIAL')\"（括号内无多余空格），"
            f"实际输出：\n{result}"
        )


class TestBug4FunctionParenSpacing:
    """
    Bug 4: 函数括号空格——remove_space_before_paren中
    re.sub(r'(\\w+)\\s+\\(', r'\\1(', text)错误移除了函数名与(间的空格。
    """

    def test_function_name_space_before_paren_preserved(self):
        """
        格式化函数名与括号之间有空格的SQL，
        断言输出保留函数名与括号间的空格，同时移除括号内侧空格：IFNULL (col, 0)。

        Validates: Requirements 1.4
        """
        sql = "SELECT IFNULL ( col, 0 ) FROM t"
        result = format_sql(sql)
        # 断言函数名与括号间空格保留，括号内侧空格移除
        assert "IFNULL (col, 0)" in result, (
            f"期望输出包含 \"IFNULL (col, 0)\"（保留函数名与括号间空格，移除括号内侧空格），"
            f"实际输出：\n{result}"
        )
