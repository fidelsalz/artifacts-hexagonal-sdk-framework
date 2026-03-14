"""Persistent multi-turn conversation session backed by ClaudeSDKClient."""
from __future__ import annotations

from typing import AsyncGenerator

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    SystemMessage,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)

from .config import get_agent_config


class ConversationSession:
    """Maintains a persistent Claude session across multiple user turns."""

    def __init__(self, agent_id: str) -> None:
        cfg = get_agent_config(agent_id)   # raises ValueError if unknown
        self._cfg = cfg
        self._options = ClaudeAgentOptions(
            cwd=cfg.cwd,
            allowed_tools=cfg.allowed_tools,
            model=cfg.model,
            permission_mode=cfg.permission_mode,
            add_dirs=[cfg.coding_dir] if cfg.coding_dir else [],
        )
        self._client = ClaudeSDKClient(self._options)
        self.turn_count = 0

    async def connect(self) -> None:
        await self._client.connect()

    async def send_message(self, text: str) -> AsyncGenerator[dict, None]:
        await self._client.query(text)
        async for message in self._client.receive_response():
            if isinstance(message, SystemMessage):
                yield {
                    "type": "system",
                    "model":           message.data.get("model"),
                    "session_id":      message.data.get("session_id"),
                    "cwd":             message.data.get("cwd"),
                    "permission_mode": message.data.get("permissionMode"),
                }
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield {"type": "assistant", "text": block.text}
            elif isinstance(message, ResultMessage):
                self.turn_count += 1
                usage = message.usage or {}
                yield {
                    "type":           "result",
                    "session_id":     message.session_id,
                    "duration_ms":    message.duration_ms,
                    "num_turns":      message.num_turns,
                    "total_cost_usd": message.total_cost_usd,
                    "input_tokens":   usage.get("input_tokens", 0),
                    "output_tokens":  usage.get("output_tokens", 0),
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                }

    async def interrupt(self) -> None:
        await self._client.interrupt()

    async def reset(self) -> None:
        """Disconnect and reconnect for a fresh context-free session."""
        await self._client.disconnect()
        self._client = ClaudeSDKClient(self._options)
        await self._client.connect()
        self.turn_count = 0

    async def disconnect(self) -> None:
        await self._client.disconnect()
