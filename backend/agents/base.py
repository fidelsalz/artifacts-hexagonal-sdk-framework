from abc import ABC, abstractmethod
from typing import AsyncGenerator


class AgentBase(ABC):
    async def pre_run(self) -> AsyncGenerator[dict, None]:
        """Optional setup phase. Override to yield status dicts."""
        return
        yield  # make it an async generator

    @abstractmethod
    async def run_stream(self) -> AsyncGenerator[dict, None]:
        """Core agent logic. Must yield event dicts."""
        ...

    async def post_run(self) -> AsyncGenerator[dict, None]:
        """Optional cleanup phase. Override to yield status dicts."""
        return
        yield  # make it an async generator

    async def execute(self) -> AsyncGenerator[dict, None]:
        """Chain pre_run → run_stream → post_run."""
        async for event in self.pre_run():
            yield event
        async for event in self.run_stream():
            yield event
        async for event in self.post_run():
            yield event
