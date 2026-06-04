"""排查会话编排 - 管理多轮对话流程，包含 DebugWorker 用于工作线程。"""

import json
import threading
from typing import Callable

from PySide6.QtCore import QObject, Signal

from core.ai_debug.deepseek_client import DeepSeekClient
from core.ai_debug.doris_connector import DorisConnector

# ── Tools 定义 ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": (
                "在 Doris 数据库上执行一条只读 SQL（SELECT / DESC / SHOW TABLES）。"
                "只用于查询数据和表结构，禁止 DDL/DML。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的 SQL 语句，仅限 SELECT、DESC、SHOW TABLES",
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么需要执行这条 SQL（简要说明排查思路）",
                    },
                },
                "required": ["sql", "reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "report_finding",
            "description": (
                "找到根因后，报告排查结论和修复方案，结束排查。"
                "只有在确定根因后才能调用此函数。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "root_cause": {
                        "type": "string",
                        "description": (
                            "【根因】为什么没查到数据（哪个表缺数据/哪个条件不满足）。"
                            "用纯文本分点列出：1. 哪个表/JOIN 出了问题 2. 具体缺什么数据 3. 数据链路断裂点。"
                            "禁止使用 markdown（**、`、``` 等），只输出纯文本。"
                        ),
                    },
                    "fix_sql": {
                        "type": "string",
                        "description": (
                            "【修复】基于 MySQL 语法的 INSERT 或 UPDATE 语句，用于写入 MySQL 源表。"
                            "可以多条，用分号分隔。"
                            "注意：修复 SQL 写入的是 MySQL 表，不是 Doris。"
                            "Doris 是查询端，通过 Flink 从 MySQL 同步数据。"
                            "因此修复 SQL 中禁止出现 op_flag / sr_update 等 Doris 专属字段。"
                            "表名必须带库名前缀，例如 post_loan.t_duebill_detail。"
                            "如果无法给出修复 SQL，填空字符串或说明原因（如'无法确定修复方案'），不要编造。"
                        ),
                    },
                },
                "required": ["root_cause", "fix_sql"],
                "additionalProperties": False,
            },
        },
    },
]

SYSTEM_PROMPT = """你是一个 Doris 数据库排障专家。用户提供一段 SQL 和期望查到但没查到的数据描述。
本工具的前提：SQL 逻辑是正确的，问题出在数据侧（缺数据 / 数据不对）。因此修复方案通常是 INSERT/UPDATE 语句。

你可以使用 execute_sql 工具在 Doris 上执行只读查询（SELECT / DESC / SHOW TABLES）。
每次只能执行一条 SQL，不要在一次调用中包含多条语句。
分析数据后，当你确定根因时，使用 report_finding 报告结论。

排查策略：
- 先查看涉及的表结构（DESC）
- 从 WHERE 条件和 JOIN 关联条件入手
- 每次查询尽量精炼（SELECT 返回行数 ≤ 20）
- 不要生成 CREATE/ALTER/DROP 语句

report_finding 的 root_cause 字段：
- 用纯文本，禁止使用 markdown（**、`、``` 等不会渲染，只会显示为乱码）
- 按逻辑分点列出，例如：
  1. 哪个表 / 哪个 JOIN 导致无结果
  2. 具体缺失了什么数据（行/字段值）
  3. 数据链路在哪里断了

report_finding 的 fix_sql 字段：
- 给出的 INSERT 或 UPDATE 必须基于 MySQL 语法，不是 Doris
- Doris 是查询端，通过 Flink 从 MySQL 同步数据。写入只能在 MySQL 源表上进行
- 禁止出现 op_flag / sr_update 等 Doris 专属字段。DESC 结果的字段中去掉这两列，就是 MySQL 的字段
- 表名必须带库名前缀。例如你在 Doris 里 DESC post_loan.t_duebill_detail，修复 SQL 就写 INSERT INTO post_loan.t_duebill_detail，不要写成 INSERT INTO t_duebill_detail
- 如果确实无法给出修复 SQL，填空字符串或说明原因，不要编造"""

# ── DebugWorker (QObject for QThread) ────────────────────────────────────────

class DebugWorker(QObject):
    """工作线程中的 Worker，负责编排排查流程并向主线程发信号。"""

    # 流式文本
    thinking = Signal(str)
    # tool 调用开始 (tool_name, reason)
    tool_call_start = Signal(str, str)
    # tool 结果 (tool_name, result_summary)
    tool_call_result = Signal(str, str)
    # 轮次进度 (current, max)
    round_count = Signal(int, int)
    # 排查结论
    finding_ready = Signal(dict)
    # 可恢复的错误
    error = Signal(str)
    # 流程结束
    done = Signal()

    MAX_ROUNDS = 20
    MAX_TOTAL_ROUNDS = 40

    def __init__(self, config: dict, sql: str, expectation: str):
        super().__init__()
        self._config = config
        self._sql = sql
        self._expectation = expectation
        self._stop_event = threading.Event()
        self._total_rounds_used = 0  # 总轮次（跨"继续排查"不重置）

    def set_stop_event(self, event: threading.Event):
        self._stop_event = event

    def run(self):
        """在主循环中执行排查流程（在工作线程中调用）。"""
        try:
            ds_client = DeepSeekClient(self._config["deepseek"])
            connector = DorisConnector(self._config["doris"])

            try:
                connector.connect()
                session = _DebugSessionCore(
                    ds_client, connector, self._total_rounds_used,
                    self.MAX_ROUNDS, self.MAX_TOTAL_ROUNDS,
                )
                result = session.run(
                    self._sql, self._expectation,
                    lambda text: self.thinking.emit(text),
                    lambda name, reason: self.tool_call_start.emit(name, reason),
                    lambda name, summary: self.tool_call_result.emit(name, summary),
                    lambda cur, limit: self.round_count.emit(cur, limit),
                    self._stop_event,
                )
                self._total_rounds_used = session.total_rounds_used
            finally:
                connector.close()

            if result:
                self.finding_ready.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.done.emit()


# ── 内部会话核心 ────────────────────────────────────────────────────────────

class _DebugSessionCore:
    """编排一次完整的排查对话（不含 Qt 依赖，可在任意线程使用）。"""

    def __init__(self, client, connector, total_rounds_used, max_rounds, max_total):
        self._client = client
        self._connector = connector
        self._total_rounds_used = total_rounds_used
        self._max_rounds = max_rounds
        self._max_total = max_total
        self._current_rounds = 0
        self._consecutive_no_tool = 0

    @property
    def total_rounds_used(self):
        return self._total_rounds_used

    def run(self, sql, expectation, stream_cb, tool_cb, result_cb, round_cb, stop_event):
        messages = self._build_initial_messages(sql, expectation)
        finding = None

        while True:
            if stop_event.is_set():
                return None

            # 检查总轮次上限
            if self._total_rounds_used >= self._max_total:
                round_cb(self._total_rounds_used, self._max_total)
                return None

            round_cb(self._total_rounds_used, self._max_total)

            response = self._client.chat_stream(messages, TOOLS, stream_cb)

            if stop_event.is_set():
                return None

            # 解析响应
            if "tool_calls" in response:
                self._consecutive_no_tool = 0
                messages.append(response["assistant_message"])

                for tc in response["tool_calls"]:
                    func = tc["function"]
                    name = func["name"]
                    args = json.loads(func["arguments"])

                    if name == "execute_sql":
                        tool_cb(name, args.get("reason", "执行 SQL 查询"))
                        result_text = self._connector.execute(args["sql"])
                        result_cb(name, self._summarize_result(result_text))
                        messages.append(self._format_tool_result(tc["id"], name, result_text))

                    elif name == "report_finding":
                        tool_cb(name, "报告排查结论")
                        result_cb(name, f"根因: {args.get('root_cause', '')}")
                        finding = {
                            "root_cause": args.get("root_cause", ""),
                            "fix_sql": args.get("fix_sql", ""),
                        }
                        messages.append(
                            self._format_tool_result(tc["id"], name, "结论已记录")
                        )
                        return finding
            else:
                # 纯文本回复
                self._consecutive_no_tool += 1
                messages.append({
                    "role": "assistant",
                    "content": response.get("content", ""),
                })

                if self._consecutive_no_tool >= 2:
                    messages.append({
                        "role": "user",
                        "content": "请使用 execute_sql 查询数据来验证你的假设",
                    })
                    self._consecutive_no_tool = 0

            self._current_rounds += 1
            self._total_rounds_used += 1

            if self._current_rounds >= self._max_rounds:
                return None  # 达到单轮上限，暂停让用户决定

    def _build_initial_messages(self, sql, expectation):
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"以下是我要排查的 SQL：\n\n```sql\n{sql}\n```\n\n"
                    f"我期望能查到的数据：{expectation}"
                ),
            },
        ]

    @staticmethod
    def _format_tool_result(tool_call_id, name, content):
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
        }

    @staticmethod
    def _summarize_result(text):
        """提取结果摘要（最多 200 字符）。"""
        text = text.strip()
        if len(text) <= 200:
            return text
        return text[:200] + "\n... (结果已截断用于显示)"
