from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()


def _safe_path(raw: str) -> Path:
    """Resolve and return a Path; raise 400 if the string is empty."""
    if not raw:
        raise HTTPException(status_code=400, detail="path is required")
    return Path(raw).resolve()


@router.get("/api/files/list")
async def list_dir(path: str = Query(...)):
    p = _safe_path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {p}")
    if not p.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {p}")

    dirs, files = [], []
    for entry in p.iterdir():
        item = {"name": entry.name, "type": "dir" if entry.is_dir() else "file", "path": str(entry.resolve())}
        (dirs if entry.is_dir() else files).append(item)

    dirs.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    return {"path": str(p), "entries": dirs + files}


@router.get("/api/files/read")
async def read_file(path: str = Query(...)):
    p = _safe_path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {p}")
    if not p.is_file():
        raise HTTPException(status_code=400, detail=f"Not a file: {p}")
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"path": str(p), "content": content}


class WriteBody(BaseModel):
    path: str
    content: str


@router.post("/api/files/write")
async def write_file(body: WriteBody):
    p = _safe_path(body.path)
    if not p.parent.exists():
        raise HTTPException(status_code=400, detail=f"Parent directory does not exist: {p.parent}")
    try:
        p.write_text(body.content, encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}
