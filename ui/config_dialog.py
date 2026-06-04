"""配置编辑弹窗 - Modal 对话框编辑 config.json。"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QPushButton, QGroupBox, QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from core.ai_debug.config_manager import ConfigManager


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 排障 - 设置")
        self.setMinimumWidth(480)
        self.setModal(True)

        try:
            config = ConfigManager.load()
        except Exception:
            config = ConfigManager.template()

        self._build_ui(config)

        # 点击取消不保存
        self._saved = False

    def _build_ui(self, config: dict):
        layout = QVBoxLayout(self)

        # ── DeepSeek API 分组 ──
        ds_group = QGroupBox("DeepSeek API")
        ds_form = QFormLayout(ds_group)

        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.Password)
        self._api_key.setText(config["deepseek"].get("api_key", ""))
        eye_btn = QPushButton("👁")
        eye_btn.setFixedWidth(28)
        eye_btn.setCheckable(True)
        eye_btn.toggled.connect(lambda checked: self._api_key.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        row = QHBoxLayout()
        row.addWidget(self._api_key)
        row.addWidget(eye_btn)
        ds_form.addRow("API Key:", row)

        self._base_url = QLineEdit()
        self._base_url.setText(config["deepseek"].get("base_url", "https://api.deepseek.com"))
        ds_form.addRow("Base URL:", self._base_url)

        self._model = QLineEdit()
        self._model.setText(config["deepseek"].get("model", "deepseek-v4-pro"))
        ds_form.addRow("Model:", self._model)

        layout.addWidget(ds_group)

        # ── Doris 数据库分组 ──
        doris_group = QGroupBox("Doris 数据库")
        doris_form = QFormLayout(doris_group)

        doris = config["doris"]
        self._host = QLineEdit()
        self._host.setText(doris.get("host", ""))
        doris_form.addRow("Host:", self._host)

        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(int(doris.get("port", 9030)))
        doris_form.addRow("Port:", self._port)

        self._user = QLineEdit()
        self._user.setText(doris.get("user", ""))
        doris_form.addRow("User:", self._user)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setText(doris.get("password", ""))
        doris_form.addRow("Password:", self._password)

        self._database = QLineEdit()
        self._database.setText(doris.get("database", ""))
        doris_form.addRow("Database:", self._database)

        self._catalog = QLineEdit()
        self._catalog.setText(doris.get("catalog", "default_catalog"))
        doris_form.addRow("Catalog:", self._catalog)

        layout.addWidget(doris_group)

        # ── 按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        """校验字段并保存。"""
        errors = []

        if not self._api_key.text().strip():
            errors.append("API Key 不能为空")
        if not self._base_url.text().strip():
            errors.append("Base URL 不能为空")
        if not self._model.text().strip():
            errors.append("Model 不能为空")
        if not self._host.text().strip():
            errors.append("Host 不能为空")
        if not self._user.text().strip():
            errors.append("User 不能为空")
        if not self._password.text().strip():
            errors.append("Password 不能为空")
        if not self._database.text().strip():
            errors.append("Database 不能为空")

        if errors:
            QMessageBox.warning(self, "校验失败", "\n".join(errors))
            return

        new_config = {
            "deepseek": {
                "api_key": self._api_key.text().strip(),
                "base_url": self._base_url.text().strip(),
                "model": self._model.text().strip(),
            },
            "doris": {
                "host": self._host.text().strip(),
                "port": self._port.value(),
                "user": self._user.text().strip(),
                "password": self._password.text().strip(),
                "database": self._database.text().strip(),
                "catalog": self._catalog.text().strip(),
            },
        }

        try:
            ConfigManager.save(new_config)
            self._saved = True
            QMessageBox.information(self, "成功", "配置已保存")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))
