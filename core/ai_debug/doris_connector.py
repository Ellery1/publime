"""Doris 连接器 - 通过 PyMySQL 执行只读查询，代码层拦截非法 SQL。"""

from __future__ import annotations

import re
import pymysql


class DorisError(Exception):
    """Doris 连接/查询异常。"""

    pass


class DorisConnector:
    # 允许的 SQL 类型（首词匹配）
    _ALLOWED_PREFIXES = re.compile(
        r"^\s*(SELECT|DESC\b|DESCRIBE\b|SHOW\b)", re.IGNORECASE
    )
    # 多语句检测
    _MULTI_STMT_PATTERN = re.compile(r";\s*(SELECT|DESC|DESCRIBE|SHOW|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", re.IGNORECASE)

    _MAX_ROWS = 20

    def __init__(self, config: dict):
        """
        config = config["doris"] 子字典。
        """
        self._host = config["host"]
        self._port = int(config.get("port", 9030))
        self._user = config["user"]
        self._password = config["password"]
        self._database = config.get("database", "")
        self._catalog = config.get("catalog", "default_catalog")
        self._conn: pymysql.Connection | None = None

    def connect(self) -> None:
        """建立 pymysql 连接，失败抛 DorisError。"""
        try:
            self._conn = pymysql.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database,
                charset="utf8mb4",
                connect_timeout=10,
                read_timeout=30,
                autocommit=True,
            )
        except pymysql.Error as e:
            raise DorisError(f"Doris 连接失败 ({self._host}:{self._port}): {e}") from e

    def close(self) -> None:
        """关闭连接。"""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def execute(self, sql: str) -> str:
        """
        校验 → 执行 → 格式化结果。

        1. 正则校验 SQL 首词，拦截非法语句
        2. 检测多语句并拦截
        3. 执行查询，取前 MAX_ROWS+1 行
        4. 按约定格式返回字符串
        """
        if self._conn is None:
            raise DorisError("未建立数据库连接")

        # 1. 校验 SQL 首词
        if not self._ALLOWED_PREFIXES.match(sql):
            return "拒绝执行：仅允许 SELECT / DESC / SHOW TABLES 语句"

        # 2. 检测多语句
        if self._MULTI_STMT_PATTERN.search(sql):
            return "拒绝执行：每次只能执行一条 SQL 语句"

        # 3. 判断 SQL 类型
        sql_type = self._detect_type(sql)

        try:
            with self._conn.cursor() as cursor:
                cursor.execute(sql)

                if sql_type == "SELECT":
                    rows = cursor.fetchmany(self._MAX_ROWS + 1)
                    if not rows:
                        return "查询返回 0 行"

                    col_names = [desc[0] for desc in cursor.description]
                    formatted = self._format_table(col_names, rows)

                    if len(rows) > self._MAX_ROWS:
                        # 取前 MAX_ROWS 行
                        rows = rows[: self._MAX_ROWS]
                        formatted = self._format_table(col_names, rows)
                        # 获取总行数估算
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM ({sql}) AS _cnt")
                            total = cursor.fetchone()[0]
                        except Exception:
                            total = "?"
                        formatted += f"\n... 共 {total} 行（已截断）\n"
                    return formatted

                else:
                    # DESC / SHOW - 不限制行数
                    rows = cursor.fetchall()
                    if not rows:
                        return "查询返回 0 行"

                    col_names = [desc[0] for desc in cursor.description]
                    return self._format_table(col_names, rows)

        except pymysql.Error as e:
            return f"执行错误: {e}"

    @staticmethod
    def _detect_type(sql: str) -> str:
        """检测 SQL 类型。"""
        upper = sql.strip().upper()
        if upper.startswith("SELECT"):
            return "SELECT"
        if upper.startswith("DESC") or upper.startswith("DESCRIBE"):
            return "DESC"
        if upper.startswith("SHOW"):
            return "SHOW"
        return "OTHER"

    @staticmethod
    def _format_table(columns: list, rows: list) -> str:
        """将查询结果格式化为 Markdown 表格。"""
        if not rows:
            return "查询返回 0 行"

        # 表头
        header = "| " + " | ".join(str(c) for c in columns) + " |"
        sep = "|---" * len(columns) + "|"
        lines = [header, sep]

        for row in rows:
            line = "| " + " | ".join(str(v) if v is not None else "NULL" for v in row) + " |"
            lines.append(line)

        return "\n".join(lines) + "\n"
