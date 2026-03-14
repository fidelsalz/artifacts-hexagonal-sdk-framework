from asyncio import Queue

active_connections: set[Queue] = set()


async def broadcast(message: str) -> None:
    for queue in list(active_connections):
        try:
            await queue.put(message)
        except Exception as e:
            print(f"Error broadcasting to client: {e}")
