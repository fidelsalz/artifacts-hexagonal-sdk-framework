import asyncio

async def my_task_stream():
    yield "Starting task..."
    await asyncio.sleep(1)

    yield "Step 1 completed."
    await asyncio.sleep(1)

    yield "Step 2 completed."
    await asyncio.sleep(1)

    yield "Task finished!"
