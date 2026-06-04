"""DeepSeek 客户端 - 使用 urllib 直接调用 DeepSeek API（兼容 OpenAI 格式），支持流式。"""

from __future__ import annotations

import json
import ssl
import urllib.request
from typing import Callable


class DeepSeekClient:
    def __init__(self, config: dict):
        self._api_key = config["api_key"]
        self._base_url = config["base_url"].rstrip("/")
        self._model = config.get("model", "deepseek-v4-pro")

    def chat_stream(
        self,
        messages: list,
        tools: list,
        delta_callback: Callable[[str], None],
    ) -> dict:
        """
        发起流式 chat completion。
        每收到一个 delta.content，调用 delta_callback(text)。
        最终返回 {"tool_calls": [...], "assistant_message": {...}} 或 {"content": "..."}。
        """
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            method="POST",
        )

        ctx = ssl.create_default_context()
        content_parts = []
        tool_calls_map: dict[int, dict] = {}

        with urllib.request.urlopen(req, context=ctx) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]  # strip "data: "
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if not chunk.get("choices"):
                    continue

                delta = chunk["choices"][0].get("delta", {})

                # 纯文本 delta
                if delta.get("content"):
                    content_parts.append(delta["content"])
                    delta_callback(delta["content"])

                # tool_calls delta
                if delta.get("tool_calls"):
                    for tc in delta["tool_calls"]:
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": "",
                                "function": {"name": "", "arguments": ""},
                            }
                        entry = tool_calls_map[idx]
                        if tc.get("id"):
                            entry["id"] += tc["id"]
                        if tc.get("function"):
                            if tc["function"].get("name"):
                                entry["function"]["name"] += tc["function"]["name"]
                            if tc["function"].get("arguments"):
                                entry["function"]["arguments"] += tc["function"]["arguments"]

        if tool_calls_map:
            tool_calls = [
                {
                    "id": v["id"],
                    "type": "function",
                    "function": {
                        "name": v["function"]["name"],
                        "arguments": v["function"]["arguments"],
                    },
                }
                for v in tool_calls_map.values()
            ]
            return {
                "tool_calls": tool_calls,
                "assistant_message": {
                    "role": "assistant",
                    "content": "".join(content_parts) if content_parts else None,
                    "tool_calls": tool_calls,
                },
            }

        return {"content": "".join(content_parts)}
