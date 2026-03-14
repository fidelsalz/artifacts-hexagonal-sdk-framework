import asyncio
from asyncio import Queue

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.sse import active_connections, broadcast
from test import my_task_stream

router = APIRouter()


@router.options("/run-task")
async def options_run_task():
    """Handle CORS preflight requests for EventSource."""
    return {"status": "ok"}


@router.get("/run-task")
async def run_task():
    """SSE endpoint that streams task progress to connected clients."""
    local_queue: Queue = Queue()
    active_connections.add(local_queue)

    async def event_generator():
        try:
            yield "data: Connected to task stream\n\n"
            while True:
                try:
                    message = await asyncio.wait_for(local_queue.get(), timeout=15.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
        finally:
            active_connections.discard(local_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/test-task")
async def start_test_task():
    """Trigger a test task that broadcasts to all SSE clients."""
    asyncio.create_task(broadcast_task())
    return {"status": "started", "message": "Test task initiated"}


async def broadcast_task():
    try:
        async for message in my_task_stream():
            await broadcast(message)
    except Exception as e:
        await broadcast(f"Task error: {str(e)}")
