"""Generic validator agent — shared by ports-validator, hexagon-validator,
adapters-validator, infra-validator.

Runs after its paired coding agent (no rollback needed — read-only by design).

Instantiate with the validator id from agents-config.yaml:
    agent = ValidatorAgent("ports-validator")
    agent = ValidatorAgent("hexagon-validator")
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
from .config import get_validator_config, AgentConfig, ValidatorConfig


class ValidatorAgent(AgentBase):

    def __init__(self, validator_id: str) -> None:
        self._validator_id = validator_id
        self._parent: AgentConfig | None = None
        self._cfg: ValidatorConfig | None = None

    def _load(self) -> tuple[AgentConfig, ValidatorConfig]:
        if self._cfg is None:
            self._parent, self._cfg = get_validator_config(self._validator_id)
        return self._parent, self._cfg  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def pre_run(self) -> AsyncGenerator[dict, None]:
        _, cfg = self._load()
        yield {"type": "status", "agent": cfg.id, "message": f"[{cfg.name}] Starting validation..."}

    async def run_stream(self) -> AsyncGenerator[dict, None]:
        parent, cfg = self._load()
        async for message in query(
            prompt=cfg.basic_prompt,
            options=ClaudeAgentOptions(
                cwd=cfg.cwd,
                allowed_tools=cfg.allowed_tools,
                model=cfg.model,
                permission_mode=cfg.permission_mode,
                add_dirs=[parent.coding_dir] if parent.coding_dir else [],
            ),
        ):
            if isinstance(message, SystemMessage):
                yield {
                    "type": "system",
                    "agent": cfg.id,
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
                        yield {"type": "assistant", "agent": cfg.id, "text": block.text}

            elif isinstance(message, UserMessage):
                yield {"type": "user", "agent": cfg.id}

            elif isinstance(message, ResultMessage):
                usage = message.usage or {}
                yield {
                    "type": "result",
                    "agent": cfg.id,
                    "session_id": message.session_id,
                    "duration_ms": message.duration_ms,
                    "num_turns": message.num_turns,
                    "total_cost_usd": message.total_cost_usd,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                }

    async def post_run(self) -> AsyncGenerator[dict, None]:
        _, cfg = self._load()
        yield {"type": "status", "agent": cfg.id, "message": f"[{cfg.name}] Validation complete."}
