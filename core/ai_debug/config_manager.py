"""配置管理模块 - 读写 config.json 并提供校验。"""

from __future__ import annotations

import json
import os
from pathlib import Path


class ConfigError(Exception):
    """配置相关异常，携带缺失字段列表。"""

    def __init__(self, message: str, missing_fields: list | None = None):
        super().__init__(message)
        self.missing_fields = missing_fields or []


class ConfigManager:
    CONFIG_PATH = Path("config.json")

    @staticmethod
    def load() -> dict:
        """
        读取 config.json，校验必填字段，缺失则抛 ConfigError。
        """
        if not ConfigManager.CONFIG_PATH.exists():
            raise ConfigError(
                "config.json 不存在",
                missing_fields=["deepseek.api_key", "doris.host", "doris.user", "doris.password"],
            )

        try:
            with open(ConfigManager.CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"config.json 格式错误: {e}")

        missing = []
        for key, path in [
            ("deepseek", "deepseek"),
            ("doris", "doris"),
        ]:
            if key not in config or not isinstance(config[key], dict):
                missing.append(key)
                continue
            section = config[key]
            if key == "deepseek":
                for field in ["api_key", "base_url", "model"]:
                    if not section.get(field):
                        missing.append(f"deepseek.{field}")
            elif key == "doris":
                for field in ["host", "port", "user", "password", "database"]:
                    if field == "port":
                        if not section.get("port"):
                            missing.append("doris.port")
                    elif not section.get(field):
                        missing.append(f"doris.{field}")

        if missing:
            raise ConfigError(
                f"config.json 缺少必填字段: {', '.join(missing)}",
                missing_fields=missing,
            )

        return config

    @staticmethod
    def save(config: dict) -> None:
        """写入 config.json。"""
        with open(ConfigManager.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    @staticmethod
    def template() -> dict:
        """返回默认模板。"""
        return {
            "deepseek": {
                "api_key": "",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-pro",
            },
            "doris": {
                "host": "",
                "port": 9030,
                "user": "",
                "password": "",
                "database": "",
                "catalog": "default_catalog",
            },
        }
