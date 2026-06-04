"""AI 排障对话框 - 独立 Modeless 对话框，详见 specs/ai-debug-tab.md。"""

from __future__ import annotations

import threading

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QTextBrowser, QPushButton, QLabel, QGroupBox,
    QMessageBox, QSplitter,
)
from PySide6.QtCore import Qt, QThread

from core.doris_log_processor import process_doris_log
from core.ai_debug.config_manager import ConfigManager, ConfigError
from core.ai_debug.debug_session import DebugWorker


class AiDebugDialog(QDialog):
    """AI 排障单例对话框。"""

    _instance = None

    @classmethod
    def get_instance(cls, parent=None):
        """获取单例。如果已存在则激活已有窗口。"""
        if cls._instance is not None:
            cls._instance.raise_()
            cls._instance.activateWindow()
            return cls._instance
        cls._instance = cls(parent)
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 排障 - Publime")
        self.setMinimumSize(700, 600)
        self.resize(800, 750)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self._thread: QThread | None = None
        self._worker: DebugWorker | None = None
        self._stop_event: threading.Event | None = None
        self._total_rounds_used = 0

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ── SQL 输入 ──
        sql_group = QGroupBox("SQL 输入")
        sql_layout = QVBoxLayout(sql_group)
        sql_hint = QLabel("粘贴 SQL 或日志（自动识别并转换）")
        sql_hint.setStyleSheet("color: gray; font-size: 11px;")
        sql_layout.addWidget(sql_hint)
        self._sql_edit = QPlainTextEdit()
        self._sql_edit.setPlaceholderText("粘贴 SQL 或 myBatis/doris-api 日志...")
        sql_layout.addWidget(self._sql_edit)
        layout.addWidget(sql_group)

        # ── 期望描述 ──
        expect_group = QGroupBox("期望查到什么")
        expect_layout = QVBoxLayout(expect_group)
        self._expect_edit = QPlainTextEdit()
        self._expect_edit.setPlaceholderText("用自然语言描述你期望能查到什么样的数据...")
        self._expect_edit.setFixedHeight(72)
        expect_layout.addWidget(self._expect_edit)
        layout.addWidget(expect_group)

        # ── 按钮行 ──
        btn_row = QHBoxLayout()

        self._settings_btn = QPushButton("设置")
        self._settings_btn.clicked.connect(self._on_settings)
        btn_row.addWidget(self._settings_btn)

        btn_row.addStretch()

        self._start_btn = QPushButton("开始排查")
        self._start_btn.clicked.connect(self._on_start)
        self._start_btn.setDefault(True)
        btn_row.addWidget(self._start_btn)

        layout.addLayout(btn_row)

        # ── 排查过程 + 结论（用 QSplitter 分隔） ──
        splitter = QSplitter(Qt.Vertical)

        # 排查过程
        process_group = QGroupBox("排查过程")
        process_layout = QVBoxLayout(process_group)
        self._output = QTextBrowser()
        self._output.setOpenExternalLinks(False)
        self._output.setReadOnly(True)
        process_layout.addWidget(self._output)
        splitter.addWidget(process_group)

        # 排查结论（排查完成后显示）
        conclusion_group = QGroupBox("排查结论")
        conclusion_layout = QVBoxLayout(conclusion_group)
        self._conclusion = QTextBrowser()
        self._conclusion.setOpenExternalLinks(False)
        self._conclusion.setReadOnly(True)
        conclusion_layout.addWidget(self._conclusion)
        conclusion_group.setVisible(False)
        splitter.addWidget(conclusion_group)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([400, 150])
        layout.addWidget(splitter, 1)

        # ── 底部按钮 ──
        bottom_row = QHBoxLayout()

        self._stop_btn = QPushButton("停止")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setVisible(False)
        bottom_row.addWidget(self._stop_btn)

        bottom_row.addStretch()

        self._continue_btn = QPushButton("继续排查")
        self._continue_btn.clicked.connect(self._on_continue)
        self._continue_btn.setVisible(False)
        bottom_row.addWidget(self._continue_btn)

        layout.addLayout(bottom_row)

    # ── 公共方法 ──

    def set_sql_text(self, text: str):
        """外部调用：预填 SQL 输入框（编辑器选中文本）。"""
        self._sql_edit.setPlainText(text)

    # ── 内部方法 ──

    def _on_settings(self):
        from ui.config_dialog import ConfigDialog
        dlg = ConfigDialog(self)
        dlg.exec()

    def _on_start(self):
        """开始排查。"""
        try:
            config = ConfigManager.load()
        except ConfigError as e:
            QMessageBox.warning(self, "配置错误", str(e))
            from ui.config_dialog import ConfigDialog
            dlg = ConfigDialog(self)
            if dlg.exec():
                try:
                    config = ConfigManager.load()
                except ConfigError:
                    return
            else:
                return

        sql_text = self._sql_edit.toPlainText().strip()
        if not sql_text:
            QMessageBox.warning(self, "输入为空", "请粘贴 SQL 或日志")
            return

        log_markers = ["执行sql:", "Preparing:", "执行参数:", "Parameters:"]
        if any(marker in sql_text for marker in log_markers):
            success, result = process_doris_log(sql_text)
            if not success:
                QMessageBox.warning(self, "日志转换失败", result)
                return
            self._output.append(
                '<span style="color: gray;">--- 日志已自动转换为 SQL ---</span>'
            )
            sql_text = result

        expectation = self._expect_edit.toPlainText().strip()
        if not expectation:
            QMessageBox.warning(self, "输入为空", "请描述你期望查到什么样的数据")
            return

        # 切换到排查状态
        self._sql_edit.setEnabled(False)
        self._expect_edit.setEnabled(False)
        self._start_btn.setVisible(False)
        self._settings_btn.setEnabled(False)
        self._stop_btn.setVisible(True)
        self._continue_btn.setVisible(False)

        self._output.clear()
        self._conclusion.clear()
        self._conclusion.parent().setVisible(False)
        self._output.append(
            '<span style="color: gray;">--- 开始排查 ---</span>'
        )

        self._stop_event = threading.Event()
        self._worker = DebugWorker(config, sql_text, expectation)
        self._worker.set_stop_event(self._stop_event)

        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._worker.thinking.connect(self._on_stream_delta)
        self._worker.tool_call_start.connect(self._on_tool_call_start)
        self._worker.tool_call_result.connect(self._on_tool_call_result)
        self._worker.round_count.connect(self._on_round_count)
        self._worker.finding_ready.connect(self._on_finding_ready)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._on_done)

        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_stop(self):
        if self._stop_event:
            self._stop_event.set()
        if self._worker:
            self._worker.done.disconnect()
            self._worker.done.connect(self._on_done_after_stop)

    def _on_continue(self):
        self._output.append(
            '<span style="color: gray;">--- 继续排查 ---</span>'
        )
        self._conclusion.clear()
        self._conclusion.parent().setVisible(False)

        try:
            config = ConfigManager.load()
        except ConfigError:
            QMessageBox.warning(self, "配置错误", "配置已失效，请重新设置")
            return

        sql_text = self._sql_edit.toPlainText().strip()
        expectation = self._expect_edit.toPlainText().strip()

        self._continue_btn.setVisible(False)
        self._stop_btn.setVisible(True)

        self._stop_event = threading.Event()
        self._worker = DebugWorker(config, sql_text, expectation)
        self._worker.set_stop_event(self._stop_event)
        self._worker._total_rounds_used = self._total_rounds_used

        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._worker.thinking.connect(self._on_stream_delta)
        self._worker.tool_call_start.connect(self._on_tool_call_start)
        self._worker.tool_call_result.connect(self._on_tool_call_result)
        self._worker.round_count.connect(self._on_round_count)
        self._worker.finding_ready.connect(self._on_finding_ready)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._on_done)

        self._thread.started.connect(self._worker.run)
        self._thread.start()

    # ── 信号槽 ──

    def _on_stream_delta(self, text: str):
        self._output.insertPlainText(text)
        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_tool_call_start(self, tool_name: str, reason: str):
        self._output.append(
            f'<br><span style="color: #4a9eff;">> {tool_name}</span>: {reason}<br>'
        )
        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_tool_call_result(self, tool_name: str, summary: str):
        color = "#2ecc71" if tool_name == "report_finding" else "#888"
        self._output.append(
            f'<span style="color: {color};">{summary}</span><br>'
        )
        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_round_count(self, current: int, limit: int):
        pass

    def _on_finding_ready(self, finding: dict):
        root_cause = finding.get("root_cause", "")
        fix_sql = finding.get("fix_sql", "")

        html = '<div style="margin: 8px 0;">'
        html += f'<p><b style="color: #c0392b;">根因</b></p>'
        html += f'<p style="white-space: pre-wrap; word-wrap: break-word;">{root_cause}</p>'

        if fix_sql:
            html += '<p style="margin-top: 12px;"><b style="color: #c0392b;">修复 SQL</b></p>'
            html += (
                f'<pre style="background: #ffffff; color: #1a6e1a; padding: 8px;'
                f' border: 1px solid #ccc; border-radius: 4px;'
                f' white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;">{fix_sql}</pre>'
            )
        else:
            html += '<p style="margin-top: 12px;"><b style="color: #c0392b;">修复 SQL</b></p>'
            html += '<p><i>（无法给出修复方案）</i></p>'
        html += '</div>'

        self._conclusion.setHtml(html)
        self._conclusion.parent().setVisible(True)

    def _on_error(self, msg: str):
        self._output.append(
            f'<br><span style="color: #e74c3c;">错误: {msg}</span><br>'
        )
        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_done(self):
        if self._worker:
            self._total_rounds_used = self._worker._total_rounds_used
        self._cleanup_thread()

        self._stop_btn.setVisible(False)
        self._continue_btn.setVisible(True)

        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_done_after_stop(self):
        if self._worker:
            self._total_rounds_used = self._worker._total_rounds_used
        self._cleanup_thread()
        self._output.append(
            '<br><span style="color: #e67e22;">--- 排查已停止 ---</span><br>'
        )
        self._reset_ui()

    def _cleanup_thread(self):
        if self._thread:
            self._thread.quit()
            self._thread.wait(3000)
            self._thread = None
        self._worker = None
        self._stop_event = None

    def _reset_ui(self):
        self._sql_edit.setEnabled(True)
        self._expect_edit.setEnabled(True)
        self._start_btn.setVisible(True)
        self._settings_btn.setEnabled(True)
        self._stop_btn.setVisible(False)
        self._continue_btn.setVisible(False)

    def closeEvent(self, event):
        if self._stop_event:
            self._stop_event.set()
        self._cleanup_thread()
        AiDebugDialog._instance = None
        super().closeEvent(event)
