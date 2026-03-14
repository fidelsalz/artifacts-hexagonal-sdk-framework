import json
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


class SampleAgent(AgentBase):
    async def pre_run(self) -> AsyncGenerator[dict, None]:
        yield {"type": "status", "message": "Setting up..."}

    async def run_stream(self) -> AsyncGenerator[dict, None]:
        async for message in query(
	            prompt="List files in your cwd.",
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Edit", "Write"],
                model="claude-haiku-4-5-20251001",
                permission_mode="acceptEdits",
            ),
        ):
            if isinstance(message, SystemMessage):
                yield {
                    "type": "system",
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
                        yield {"type": "assistant", "text": block.text}

            elif isinstance(message, UserMessage):
                yield {"type": "user"}

            elif isinstance(message, ResultMessage):
                usage = message.usage or {}
                yield {
                    "type": "result",
                    "session_id": message.session_id,
                    "duration_ms": message.duration_ms,
                    "num_turns": message.num_turns,
                    "total_cost_usd": message.total_cost_usd,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                }

    async def post_run(self) -> AsyncGenerator[dict, None]:
        yield {"type": "status", "message": "Cleaning up..."}
