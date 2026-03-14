import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse

from agents import get_agent
from agents.config import CONFIG_PATH, get_agent_config, get_validator_config
from agents.conversation_agent import ConversationSession

router = APIRouter()


@router.get("/api/agents/config-file")
async def agent_config_file():
    """Return the agents-config.yaml path and content for editing."""
    path = str(CONFIG_PATH.resolve())
    content = CONFIG_PATH.read_text(encoding="utf-8")
    return {"path": path, "content": content}


@router.get("/api/agents/{agent_name}/paths")
async def agent_paths(agent_name: str):
    """Return cwd and coding_dir for a coding agent or validator."""
    try:
        cfg = get_agent_config(agent_name)
        return {"cwd": cfg.cwd, "coding_dir": cfg.coding_dir}
    except ValueError:
        pass
    try:
        _parent, vcfg = get_validator_config(agent_name)
        return {"cwd": vcfg.cwd, "coding_dir": None}
    except ValueError:
        return JSONResponse(status_code=404, content={"detail": f"Agent {agent_name!r} not found"})


@router.get("/api/agents/{agent_name}/stream")
async def agent_stream(agent_name: str):
    """Run a named agent and stream structured events over SSE."""
    try:
        agent = get_agent(agent_name)
    except ValueError:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": f"Agent {agent_name!r} not found"})

    async def generate():
        try:
            async for event in agent.execute():
                yield f"data: {json.dumps(event)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/ws/agents/{agent_name}/chat")
async def agent_chat_ws(websocket: WebSocket, agent_name: str):
    """WebSocket conversation endpoint — persistent multi-turn Claude session."""
    await websocket.accept()

    try:
        session = ConversationSession(agent_name)
    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    await session.connect()
    await websocket.send_json({"type": "connected", "agent": agent_name})

    try:
        while True:
            data = await websocket.receive_json()
            cmd  = data.get("type")

            if cmd == "message":
                text = (data.get("text") or "").strip()
                if not text:
                    continue
                try:
                    async for event in session.send_message(text):
                        await websocket.send_json(event)
                    await websocket.send_json({"type": "turn_complete"})
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})

            elif cmd == "interrupt":
                await session.interrupt()
                await websocket.send_json({"type": "interrupted"})

            elif cmd == "new_session":
                await session.reset()
                await websocket.send_json({"type": "session_reset"})

    except WebSocketDisconnect:
        pass
    finally:
        await session.disconnect()
