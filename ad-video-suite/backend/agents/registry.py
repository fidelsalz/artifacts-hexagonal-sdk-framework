"""In-process session registry for concurrency enforcement.

In asyncio, synchronous methods with no await points cannot be interrupted by
other coroutines, so no lock is needed for these dict operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


class ConcurrencyLimitError(Exception):
    pass


@dataclass
class SessionInfo:
    session_key: str
    campaign: str
    agent_id: str
    cwd: str
    started_at: datetime


class SessionRegistry:

    def __init__(self) -> None:
        # campaign -> agent_id -> set[session_key]
        self._active: dict[str, dict[str, set[str]]] = {}
        self._info: dict[str, SessionInfo] = {}

    def acquire(
        self,
        campaign: str,
        agent_id: str,
        cwd: str,
        max_campaigns: int,
        max_concurrent: int,
    ) -> str:
        active_campaigns = set(self._active.keys())

        if campaign not in active_campaigns and len(active_campaigns) >= max_campaigns:
            names = ", ".join(sorted(active_campaigns))
            raise ConcurrencyLimitError(
                f"Max {max_campaigns} active campaigns reached ({names}). "
                f"Close a session in one of them first."
            )

        current = len(self._active.get(campaign, {}).get(agent_id, set()))
        if current >= max_concurrent:
            raise ConcurrencyLimitError(
                f"{agent_id!r} agent for campaign {campaign} is already running. "
                f"Close it before starting a new one."
            )

        key = str(uuid4())
        self._active.setdefault(campaign, {}).setdefault(agent_id, set()).add(key)
        self._info[key] = SessionInfo(
            session_key=key,
            campaign=campaign,
            agent_id=agent_id,
            cwd=cwd,
            started_at=datetime.now(timezone.utc),
        )
        return key

    def release(self, session_key: str) -> None:
        info = self._info.pop(session_key, None)
        if info is None:
            return
        agent_set = self._active.get(info.campaign, {}).get(info.agent_id)
        if agent_set is not None:
            agent_set.discard(session_key)
            if not agent_set:
                del self._active[info.campaign][info.agent_id]
            if not self._active.get(info.campaign):
                self._active.pop(info.campaign, None)

    def active_campaigns(self) -> list[str]:
        return sorted(self._active.keys())

    def snapshot(self) -> list[dict]:
        return [
            {
                "session_key": s.session_key,
                "campaign":    s.campaign,
                "agent_id":    s.agent_id,
                "cwd":         s.cwd,
                "started_at":  s.started_at.isoformat(),
            }
            for s in self._info.values()
        ]


registry = SessionRegistry()
