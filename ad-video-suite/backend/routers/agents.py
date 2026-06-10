import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

log = logging.getLogger(__name__)

from agents import get_session
from agents.config import agent_status, agents_for_folder, get_agent_config, get_base_path, get_settings, load_config, load_template_config
from agents.registry import ConcurrencyLimitError, registry
from core.promotions import promote_arc, promote_hook

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONVENTION_RE = re.compile(
    r'^C\d{3}$'         # campaign: C001
    r'|^[A-Z]{3}$'      # section:  INT, SCE, MAD
    r'|^A\d+$'          # angle:    A01
    r'|^A\d+R\d+$'      # arc:      A01R01
    r'|^A\d+R\d+H\d+$'  # hook:     A01R01H01
)
_SKIP_DIRS = {"agents", "product", "assets"}


def _build_tree(path: Path, campaign_slug: str, configs: dict, section: Optional[str] = None) -> list[dict]:
    """Recursively build tree nodes for folders matching the naming convention."""
    nodes = []
    try:
        children = sorted(p for p in path.iterdir() if p.is_dir())
    except PermissionError:
        return nodes

    # If the current path is itself a launchable folder (agents run here and
    # write output subdirs), show all its children without the naming filter.
    # Example: SCE/A01R01H01 has agents → script/, storyboard/ etc. must appear.
    parent_has_agents = any(
        re.search(cfg.cwd_pattern, path.name)
        and (not cfg.sections or section in cfg.sections)
        for cfg in configs.values()
    )

    for child in children:
        name = child.name
        if name in _SKIP_DIRS or name.startswith("."):
            continue

        # Determine section context for this child and its descendants
        child_section = name if re.match(r'^[A-Z]{3}$', name) else section

        # Apply naming filter only when the parent is not a launchable folder.
        # Inside a launchable folder every non-skipped subdir is an output dir.
        if not parent_has_agents:
            matches_agent = any(
                re.search(cfg.cwd_pattern, name)
                and (not cfg.sections or child_section in cfg.sections)
                for cfg in configs.values()
            )
            if not _CONVENTION_RE.match(name) and not matches_agent:
                continue

        available = []
        for cfg in configs.values():
            if not re.search(cfg.cwd_pattern, name):
                continue
            if cfg.sections and child_section not in cfg.sections:
                continue
            status, blocked_by = agent_status(cfg, str(child))
            available.append({
                "id":         cfg.id,
                "status":     status,
                "blocked_by": [inp.get("path", "") for inp in blocked_by],
            })
        node = {
            "name":             name,
            "path":             str(child),
            "available_agents": available,
            "children":         _build_tree(child, campaign_slug, configs, child_section),
        }
        nodes.append(node)
    return nodes


def _campaign_slug_from_path(path: str) -> Optional[str]:
    """Extract C### segment from an absolute path."""
    for part in Path(path).parts:
        if re.match(r'^C\d{3}$', part):
            return part
    return None


def _section_from_path(path: str) -> Optional[str]:
    """Extract 3-letter section code (INT, SCE, …) from an absolute path."""
    for part in Path(path).parts:
        if re.match(r'^[A-Z]{3}$', part):
            return part
    return None


# ---------------------------------------------------------------------------
# REST
# ---------------------------------------------------------------------------

@router.get("/api/agents")
async def list_agents(campaign: Optional[str] = Query(default=None)):
    """Return agent list for a campaign (or template if no campaign given)."""
    try:
        configs = load_config(campaign) if campaign else load_template_config()
    except Exception:
        configs = load_template_config()
    return [
        {
            "id":          cfg.id,
            "name":        cfg.name,
            "role":        cfg.role,
            "comm_type":   cfg.comm_type,
            "cwd_pattern": cfg.cwd_pattern,
        }
        for cfg in configs.values()
    ]


@router.get("/api/agents/{agent_name}/config")
async def agent_config(agent_name: str, campaign: Optional[str] = Query(default=None)):
    try:
        configs = load_config(campaign) if campaign else load_template_config()
        cfg = configs.get(agent_name)
        if cfg is None:
            return JSONResponse(status_code=404, content={"detail": f"Agent {agent_name!r} not found"})
        return {
            "id":          cfg.id,
            "name":        cfg.name,
            "role":        cfg.role,
            "comm_type":   cfg.comm_type,
            "cwd_pattern": cfg.cwd_pattern,
            "model":       cfg.model,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.get("/api/tree")
async def get_tree():
    """Return the full campaign tree with available_agents per node."""
    base_path = Path(get_settings().get("base_path", ""))

    if not base_path.exists():
        return []

    result = []
    for campaign_dir in sorted(base_path.iterdir()):
        if not campaign_dir.is_dir():
            continue
        slug = campaign_dir.name
        if not re.match(r'^C\d{3}$', slug):
            continue

        try:
            configs = load_config(slug)
        except Exception:
            configs = load_template_config()

        campaign_agents = [
            cfg.id for cfg in configs.values()
            if re.search(cfg.cwd_pattern, slug)
        ]

        result.append({
            "name":             slug,
            "path":             str(campaign_dir),
            "available_agents": campaign_agents,
            "children":         _build_tree(campaign_dir, slug, configs),
        })

    return result


@router.get("/api/infer-agent")
async def infer_agent(path: str = Query(...), campaign: Optional[str] = Query(default=None)):
    """Return agents whose cwd_pattern matches the last segment of the given path."""
    folder_name = Path(path).name
    slug = campaign or _campaign_slug_from_path(path)
    section = _section_from_path(path)
    matched = agents_for_folder(folder_name, slug, section)
    result = []
    for cfg in matched:
        status, blocked_by = agent_status(cfg, path)
        result.append({
            "id":         cfg.id,
            "name":       cfg.name,
            "role":       cfg.role,
            "status":     status,
            "blocked_by": [inp.get("path", "") for inp in blocked_by],
        })
    return result


class LaunchBody(BaseModel):
    path: str
    agent_id: Optional[str] = None


@router.post("/api/launch")
async def launch_agent(body: LaunchBody):
    """Resolve a folder path to a launchable agent and return the WS URL.

    If agent_id is omitted the server infers it. If multiple agents match and
    no agent_id is given, returns ambiguous=true with the candidate list so the
    UI can show a picker and re-call with agent_id set.
    """
    cwd = Path(body.path)
    if not cwd.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {body.path}")

    slug = _campaign_slug_from_path(body.path)
    section = _section_from_path(body.path)
    candidates = agents_for_folder(cwd.name, slug, section)

    if not candidates:
        raise HTTPException(status_code=400, detail=f"No agent supports this folder type: {cwd.name}")

    if body.agent_id:
        matched = [c for c in candidates if c.id == body.agent_id]
        if not matched:
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{body.agent_id}' does not support folder '{cwd.name}'. "
                       f"Valid agents here: {[c.id for c in candidates]}",
            )
        chosen = matched[0]
    elif len(candidates) == 1:
        chosen = candidates[0]
    else:
        return {
            "ambiguous":  True,
            "campaign":   slug,
            "cwd":        str(cwd),
            "candidates": [
                {"id": c.id, "name": c.name, "role": c.role, "status": agent_status(c, str(cwd))[0]}
                for c in candidates
            ],
        }

    ws_url = f"/ws/agents/{chosen.id}/chat?cwd={cwd}&campaign={slug}"
    status, _ = agent_status(chosen, str(cwd))
    return {
        "ambiguous":  False,
        "agent_id":   chosen.id,
        "agent_name": chosen.name,
        "role":       chosen.role,
        "campaign":   slug,
        "cwd":        str(cwd),
        "ws_url":     ws_url,
        "status":     status,
    }


class PromoteHookBody(BaseModel):
    path: str


@router.post("/api/promote-hook")
async def promote_hook_endpoint(body: PromoteHookBody):
    """Create SCE/{hook_id}/ and seed INT files into it.

    Expects path to be an A##R##H## folder inside the campaign's INT/ tree.
    Idempotent: files already present at the destination are skipped.
    """
    hook_path = Path(body.path)
    if not hook_path.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {body.path}")

    slug = _campaign_slug_from_path(body.path)
    if not slug:
        raise HTTPException(status_code=400, detail="Could not determine campaign slug from path")

    base_path = get_settings().get("base_path", "")
    campaign_dir = Path(base_path) / slug

    try:
        result = promote_hook(campaign_dir, hook_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


_PLATFORM_RE = re.compile(r'^[A-Z]{2,3}$')


class PromoteArcBody(BaseModel):
    path: str      # absolute path to INT arc folder (e.g. /campaigns/C001/INT/A01/A01R01)
    platform: str  # IMG platform subfolder, e.g. "ML"


@router.post("/api/promote-arc")
async def promote_arc_endpoint(body: PromoteArcBody):
    """Create IMG/{platform}/ and seed INT arc files into it.

    Expects path to be an A##R## folder inside the campaign's INT/ tree.
    Idempotent: files already present at the destination are skipped.
    """
    if not _PLATFORM_RE.match(body.platform):
        raise HTTPException(status_code=400, detail=f"Invalid platform {body.platform!r}: must be 2–3 uppercase letters")

    arc_path = Path(body.path)
    if not arc_path.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {body.path}")

    slug = _campaign_slug_from_path(body.path)
    if not slug:
        raise HTTPException(status_code=400, detail="Could not determine campaign slug from path")

    base_path = get_settings().get("base_path", "")
    campaign_dir = Path(base_path) / slug

    try:
        result = promote_arc(campaign_dir, arc_path, body.platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.get("/api/sessions")
async def list_sessions():
    """Active agent sessions — grouped by campaign."""
    return {
        "active_campaigns": registry.active_campaigns(),
        "sessions":         registry.snapshot(),
    }


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@router.websocket("/ws/agents/{agent_name}/chat")
async def agent_chat_ws(
    websocket: WebSocket,
    agent_name: str,
    cwd: str = Query(...),
    campaign: Optional[str] = Query(default=None),
):
    """Persistent WS session. cwd and campaign are required query params.

    Message protocol (client → server):
      {"type": "message",    "text": "..."}   follow-up message
      {"type": "interrupt"}                   interrupt current generation
      {"type": "new_session"}                 restart: reconnect and re-run opening task

    Events (server → client):
      {"type": "system",       ...}
      {"type": "connected",    "agent": "...", "cwd": "..."}
      {"type": "assistant",    "text": "..."}
      {"type": "result",       ...}
      {"type": "turn_complete"}
      {"type": "interrupted"}
      {"type": "session_reset"}
      {"type": "error",        "message": "..."}
    """
    await websocket.accept()

    slug = campaign or _campaign_slug_from_path(cwd)

    try:
        _pre_cfg = get_agent_config(agent_name, slug)
        _status, _blocked = agent_status(_pre_cfg, cwd)
        if _status == "blocked":
            lines = "\n".join(
                f"  • `{inp.get('path', '')}` — run the {inp.get('produced_by', 'upstream')} agent first"
                for inp in _blocked
            )
            await websocket.send_json({"type": "error", "message": f"Cannot start: missing required inputs:\n{lines}"})
            await websocket.close()
            return
    except Exception:
        pass

    log.info("[ws:%s] slug=%s cwd=%s — get_session", agent_name, slug, cwd)
    try:
        session = get_session(agent_name, cwd, slug)
    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    cfg = get_agent_config(agent_name, slug)
    max_campaigns = get_settings().get("max_active_campaigns", 3)

    log.info("[ws:%s] registry.acquire max_campaigns=%s max_concurrent=%s", agent_name, max_campaigns, cfg.max_concurrent)
    try:
        session_key = registry.acquire(slug, agent_name, cwd, max_campaigns, cfg.max_concurrent)
    except ConcurrencyLimitError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    try:
        log.info("[ws:%s] session.connect() …", agent_name)
        try:
            await session.connect()
        except Exception as e:
            log.exception("[ws:%s] session.connect() raised: %s", agent_name, e)
            await websocket.send_json({"type": "error", "message": f"Agent failed to start: {e}"})
            await websocket.close()
            return
        log.info("[ws:%s] connected — sending event", agent_name)
        await websocket.send_json({"type": "connected", "agent": agent_name, "cwd": cwd})

        log.info("[ws:%s] run_opening_task …", agent_name)
        try:
            async for event in session.run_opening_task():
                await websocket.send_json(event)
            await websocket.send_json({"type": "turn_complete"})
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

        try:
            while True:
                data = await websocket.receive_json()
                cmd = data.get("type")

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
                    try:
                        async for event in session.run_opening_task():
                            await websocket.send_json(event)
                        await websocket.send_json({"type": "turn_complete"})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "message": str(e)})

        except WebSocketDisconnect:
            pass
    finally:
        registry.release(session_key)
        await session.disconnect()
