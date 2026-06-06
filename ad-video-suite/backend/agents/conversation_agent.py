"""Persistent multi-turn conversation session for ad-video agents.

cwd is a runtime parameter chosen by the user (the folder they clicked in the tree).
No spreading or output tracking — the agent reads and writes directly in its cwd.
"""
from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
)

from .config import get_agent_config, load_mcp_override


class ConversationSession:

    def __init__(self, agent_id: str, cwd: str, campaign_slug: Optional[str] = None) -> None:
        cfg = get_agent_config(agent_id, campaign_slug)
        mcp = load_mcp_override(agent_id, campaign_slug)
        self._cfg = cfg
        self._cwd = cwd
        self._basic_prompt = cfg.basic_prompt.format(
            cwd=cwd,
            prompt_file=cfg.prompt_file,
        )
        add_dirs = [(Path(cwd) / d).resolve() for d in cfg.add_dirs]
        self._options = ClaudeAgentOptions(
            cwd=cwd,
            allowed_tools=cfg.allowed_tools,
            model=cfg.model,
            permission_mode=cfg.permission_mode,
            add_dirs=add_dirs,
            mcp_servers=mcp.get("mcp_servers", {}),
            strict_mcp_config=bool(mcp.get("strict_mcp_config", False)),
        )
        self._client = ClaudeSDKClient(self._options)
        self.turn_count = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        await self._client.connect()

    async def disconnect(self) -> None:
        await self._client.disconnect()

    async def interrupt(self) -> None:
        await self._client.interrupt()

    async def reset(self) -> None:
        """Disconnect and reconnect with a fresh subprocess."""
        await self._client.disconnect()
        self._client = ClaudeSDKClient(self._options)
        self.turn_count = 0
        await self._client.connect()

    # ------------------------------------------------------------------
    # Turns
    # ------------------------------------------------------------------

    async def run_opening_task(self) -> AsyncGenerator[dict, None]:
        """Fire basic_prompt — agent reads its cwd and executes its full task."""
        async for event in self.send_message(self._basic_prompt):
            yield event

    async def send_message(self, text: str) -> AsyncGenerator[dict, None]:
        await self._client.query(text)
        async for message in self._client.receive_response():
            if isinstance(message, SystemMessage):
                yield {
                    "type":            "system",
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
                    "type":              "result",
                    "session_id":        message.session_id,
                    "duration_ms":       message.duration_ms,
                    "num_turns":         message.num_turns,
                    "total_cost_usd":    message.total_cost_usd,
                    "input_tokens":      usage.get("input_tokens", 0),
                    "output_tokens":     usage.get("output_tokens", 0),
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                }
