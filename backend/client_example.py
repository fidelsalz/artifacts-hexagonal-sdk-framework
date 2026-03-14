"""
Example client to consume the SSE endpoint.
Run this to test the /run-task endpoint.
"""

import asyncio
import aiohttp


async def consume_sse():
    """Connect to SSE endpoint and print messages as they arrive."""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8010/run-task") as resp:
            print(f"Status: {resp.status}")
            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    message = line[6:]  # Remove "data: " prefix
                    print(f"Message: {message}")


if __name__ == "__main__":
    print("Connecting to SSE endpoint...")
    asyncio.run(consume_sse())
