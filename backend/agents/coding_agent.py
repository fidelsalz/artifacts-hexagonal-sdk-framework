"""Generic coding agent — shared by ports, hexagon, adapters, infra.

Instantiate with the agent id from agents-config.yaml:
    agent = CodingAgent("ports")
    agent = CodingAgent("hexagon")
"""
from __future__ import annotations

from typing import AsyncGenerator

from claude_agent_sdk import (
    ClaudeAgentOptions,
    query,
    SystemMessage,
    AssistantMessage,
    UserMessage,
    ResultMessage,
    TextBlock,
)

from .base import AgentBase
from .config import get_agent_config, AgentConfig
from .rollback import rollback_coding_dir, clear_out_dir


class CodingAgent(AgentBase):

    def __init__(self, agent_id: str) -> None:
        self._agent_id = agent_id
        self._cfg: AgentConfig | None = None

    @property
    def cfg(self) -> AgentConfig:
        if self._cfg is None:
            self._cfg = get_agent_config(self._agent_id)
        return self._cfg

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def pre_run(self) -> AsyncGenerator[dict, None]:
        yield {"type": "status", "message": f"[{self.cfg.name}] Starting..."}
        if self.cfg.coding_dir:
            for event in rollback_coding_dir(self.cfg.coding_dir):
                yield event
        for event in clear_out_dir(self.cfg.cwd):
            yield event

    async def run_stream(self) -> AsyncGenerator[dict, None]:
        async for message in query(
            prompt=self.cfg.basic_prompt,
            options=ClaudeAgentOptions(
                cwd=self.cfg.cwd,
                allowed_tools=self.cfg.allowed_tools,
                model=self.cfg.model,
                permission_mode=self.cfg.permission_mode,
                add_dirs=[self.cfg.coding_dir] if self.cfg.coding_dir else [],
            ),
        ):
            if isinstance(message, SystemMessage):
                yield {
                    "type": "system",
                    "agent": self.cfg.id,
                    "uuid": message.data.get("uuid"),
                    "model": message.data.get("model"),
                    "session_id": message.data.get("session_id"),
                    "cwd": message.data.get("cwd"),
                    "permission_mode": message.data.get("permissionMode"),
                    "tools_count": len(message.data.get("tools") or []),
                }

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield {"type": "assistant", "agent": self.cfg.id, "text": block.text}

            elif isinstance(message, UserMessage):
                yield {"type": "user", "agent": self.cfg.id}

            elif isinstance(message, ResultMessage):
                usage = message.usage or {}
                yield {
                    "type": "result",
                    "agent": self.cfg.id,
                    "session_id": message.session_id,
                    "duration_ms": message.duration_ms,
                    "num_turns": message.num_turns,
                    "total_cost_usd": message.total_cost_usd,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                }

    async def post_run(self) -> AsyncGenerator[dict, None]:
        yield {"type": "status", "message": f"[{self.cfg.name}] Done."}
