import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

log = logging.getLogger(__name__)

router = APIRouter()

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _track(available: bool, items: list) -> dict:
    return {"available": available, "items": items}


def _find_frame_img(directory: Path, stem: str, tag: str) -> str | None:
    """Locate a frame image trying both naming conventions: {stem}-{tag}-frame.* and {stem}-{tag}.*"""
    for pattern in (f"{stem}-{tag}-frame.*", f"{stem}-{tag}.*"):
        match = next(
            (str(x) for x in sorted(directory.glob(pattern)) if x.suffix.lower() in _IMAGE_EXTS),
            None,
        )
        if match:
            return match
    return None


def _collect_ig_attempts(ig_dir: Path) -> dict:
    """Collect image-generation attempt data for a shot's ig directory."""
    approved = []
    approved_dir = ig_dir / "approved"
    if approved_dir.is_dir():
        for p in sorted(approved_dir.iterdir()):
            if not (p.is_file() and p.suffix == ".json"):
                continue
            try:
                data = _read_json(p)
                ff = data.get("first_frame") or {}
                lf = data.get("last_frame") or {}
                stem = p.stem  # e.g. "attempt-001"
                approved.append({
                    "attempt": data.get("attempt"),
                    "model": data.get("model"),
                    "first_frame_job_id": ff.get("job_id"),
                    "last_frame_job_id": lf.get("job_id"),
                    "character_reference_job_id": data.get("character_reference_job_id"),
                    "first_frame": _find_frame_img(approved_dir, stem, "first"),
                    "last_frame": _find_frame_img(approved_dir, stem, "last"),
                })
            except Exception:
                pass

    attempts = []
    attempts_dir = ig_dir / "attempts"
    if attempts_dir.is_dir():
        seen_stems: set[str] = set()
        # JSON-first pass: collect metadata + resolve images
        for p in sorted(attempts_dir.iterdir()):
            if not (p.is_file() and p.suffix == ".json"):
                continue
            try:
                data = _read_json(p)
                stem = p.stem
                seen_stems.add(stem)
                first_frame_img = _find_frame_img(attempts_dir, stem, "first")
                last_frame_img = _find_frame_img(attempts_dir, stem, "last")
                if first_frame_img or last_frame_img:
                    attempts.append({
                        "attempt": data.get("attempt"),
                        "model": data.get("model"),
                        "first_frame": first_frame_img,
                        "last_frame": last_frame_img,
                    })
            except Exception:
                pass
        # Image-only pass: pick up images that have no JSON sidecar
        for p in sorted(attempts_dir.iterdir()):
            if not (p.is_file() and p.suffix.lower() in _IMAGE_EXTS):
                continue
            # Derive stem by stripping trailing -first/-first-frame/-last/-last-frame
            base = re.sub(r"-(first|last)(-frame)?$", "", p.stem, flags=re.IGNORECASE)
            if base in seen_stems:
                continue
            seen_stems.add(base)
            first_frame_img = _find_frame_img(attempts_dir, base, "first")
            last_frame_img = _find_frame_img(attempts_dir, base, "last")
            if first_frame_img or last_frame_img:
                attempts.append({
                    "attempt": base,
                    "model": None,
                    "first_frame": first_frame_img,
                    "last_frame": last_frame_img,
                })

    total = 0
    for sub in ("attempts", "approved", "disapproved"):
        d = ig_dir / sub
        if d.is_dir():
            total += sum(1 for p in d.iterdir() if p.is_file() and p.suffix == ".json")

    return {"approved": approved, "attempts": attempts, "attempts_count": total}


def _gen_status_and_files(cwd: Path, shot_id: str) -> dict:
    """Derive the highest generation status and collect artifact data for a shot."""
    ig_dir = cwd / "image-generation" / shot_id
    vp_approved = cwd / "video-prompts" / shot_id / "approved"
    gc_approved = cwd / "generated-clips" / shot_id / "approved"

    files = {
        "image_generation": _collect_ig_attempts(ig_dir),
        "video_url": None,
    }

    # Video URL from newest approved generated-clip JSON
    if gc_approved.is_dir():
        clip_jsons = sorted(
            p for p in gc_approved.iterdir()
            if p.is_file() and p.suffix == ".json"
        )
        for clip_json in reversed(clip_jsons):
            try:
                data = _read_json(clip_json)
                if data.get("video_url"):
                    files["video_url"] = data["video_url"]
                    break
            except Exception:
                continue

    # Determine highest status
    if gc_approved.is_dir() and any(
        p.is_file() and p.suffix == ".json" for p in gc_approved.iterdir()
    ):
        status = "generated"
    elif vp_approved.is_dir() and any(
        p.is_file() and p.suffix == ".json" for p in vp_approved.iterdir()
    ):
        status = "video_prompted"
    elif files["image_generation"]["approved"]:
        status = "imaged"
    elif ig_dir.is_dir():
        status = "prompted"
    else:
        status = "pending"

    return {"gen_status": status, "files": files}


def _load_character_asset(char_dir: Path) -> dict:
    char_json_path = char_dir / "character.json"
    approved_dir = char_dir / "approved"

    character_data = None
    if char_json_path.is_file():
        try:
            character_data = _read_json(char_json_path)
        except Exception:
            pass

    approved_image = None
    if approved_dir.is_dir():
        for p in sorted(approved_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in _IMAGE_EXTS:
                approved_image = str(p)
                break

    return {
        "available": character_data is not None,
        "higgsfield_job_id": (character_data or {}).get("higgsfield_job_id"),
        "generation_prompt": (character_data or {}).get("generation_prompt"),
        "approved_image": approved_image,
        "character_json": str(char_json_path) if character_data else None,
    }


def _load_product_asset(subdir: Path) -> dict:
    """Build product file list. Image files are included directly; JSON cache files are
    resolved to the source image via their 'filename' field in PRD/images/."""
    prd_images_dir = subdir.parent.parent.parent.parent / "PRD" / "images"
    files = []
    for p in sorted(subdir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() in _IMAGE_EXTS:
            files.append(str(p))
        elif p.suffix == ".json":
            try:
                data = _read_json(p)
                filename = data.get("filename")
                if filename:
                    img_path = prd_images_dir / filename
                    if img_path.is_file():
                        files.append(str(img_path))
            except Exception:
                pass
    return {"available": bool(files), "files": files}


def _load_assets(cwd: Path) -> dict:
    """Return available assets from the assets/ folder in the hook root."""
    assets_dir = cwd / "assets"
    if not assets_dir.is_dir():
        return {}

    result = {}
    for subdir in sorted(assets_dir.iterdir()):
        if not subdir.is_dir():
            continue
        name = subdir.name
        if name == "character":
            result["character"] = _load_character_asset(subdir)
        elif name == "product":
            result["product"] = _load_product_asset(subdir)
        else:
            files = sorted(str(p) for p in subdir.rglob("*") if p.is_file())
            result[name] = {"available": bool(files), "files": files}
    return result


def _load_script(cwd: Path) -> dict:
    path = cwd / "script" / "script.json"
    try:
        data = _read_json(path)
    except (FileNotFoundError, json.JSONDecodeError):
        return _track(False, [])

    lines = data if isinstance(data, list) else data.get("lines", [])
    items = []
    for i, line in enumerate(lines, start=1):
        items.append({
            "id": f"L{line.get('line_number', i):02d}" if isinstance(line.get("line_number"), int) else f"L{i:02d}",
            "start_s": line.get("start_s"),
            "end_s": line.get("end_s"),
            "label": line.get("text", ""),
            "phase": line.get("phase", ""),
        })
    return _track(True, items)


def _load_storyboard(cwd: Path) -> dict:
    sb_dir = cwd / "storyboard"
    moment_files = sorted(sb_dir.glob("M*.json")) if sb_dir.is_dir() else []
    if not moment_files:
        return _track(False, [])
    items = []
    for p in moment_files:
        try:
            moment = _read_json(p)
        except Exception:
            continue
        items.append({
            "id": moment.get("id", ""),
            "start_s": moment.get("start_s"),
            "end_s": moment.get("end_s"),
            "label": moment.get("visual_moment", ""),
            "purpose": moment.get("purpose", ""),
        })
    return _track(True, items)


def _load_scene_specs(cwd: Path) -> dict:
    ss_dir = cwd / "scene-specs"
    scene_files = sorted(ss_dir.glob("S*.json")) if ss_dir.is_dir() else []
    if not scene_files:
        return _track(False, [])
    items = []
    for p in scene_files:
        try:
            scene = _read_json(p)
        except Exception:
            continue
        items.append({
            "id": scene.get("scene_id", ""),
            "start_s": scene.get("start_s"),
            "end_s": scene.get("end_s"),
            "label": scene.get("subject", ""),
            "purpose": scene.get("purpose", ""),
            "mood": scene.get("mood", ""),
            "render_type": scene.get("render_type", "video"),
        })
    return _track(True, items)


def _load_shots(cwd: Path) -> dict:
    shots_dir = cwd / "shots"
    shot_files = sorted(shots_dir.glob("S*/SH*.json")) if shots_dir.is_dir() else []
    if not shot_files:
        return _track(False, [])
    items = []
    for p in shot_files:
        try:
            shot = _read_json(p)
        except Exception:
            continue
        shot_id = shot.get("shot_id", "")
        gen = _gen_status_and_files(cwd, shot_id)
        items.append({
            "id": shot_id,
            "start_s": shot.get("start_s"),
            "end_s": shot.get("end_s"),
            "label": shot.get("coverage", ""),
            "purpose": shot.get("purpose", ""),
            "render_type": shot.get("render_type", "video"),
            "gen_status": gen["gen_status"],
            "files": gen["files"],
        })
    return _track(True, items)


def _load_graphics(cwd: Path) -> dict:
    path = cwd / "graphics" / "graphics-plan.json"
    try:
        data = _read_json(path)
    except (FileNotFoundError, json.JSONDecodeError):
        return _track(False, [])

    items = []
    for g in data.get("graphics", []):
        items.append({
            "id": g.get("graphic_id", ""),
            "start_s": g.get("start_s"),
            "end_s": g.get("end_s"),
            "label": g.get("text", ""),
            "type": g.get("type", ""),
        })
    return _track(True, items)


@router.get("/api/timeline")
async def get_timeline(cwd: str = Query(...)):
    """Return time-positioned artifact tracks for an SCE hook root folder.

    Each track contains items with start_s/end_s and enough metadata to render
    a timeline slot. Shots additionally include gen_status and file paths
    passable to GET /api/files/serve for image/video rendering.
    """
    cwd_path = Path(cwd).resolve()
    if not cwd_path.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {cwd}")

    tracks = {
        "script":      _load_script(cwd_path),
        "storyboard":  _load_storyboard(cwd_path),
        "scene_specs": _load_scene_specs(cwd_path),
        "shots":       _load_shots(cwd_path),
        "graphics":    _load_graphics(cwd_path),
    }

    # Derive total duration from the highest end_s across all tracks
    all_ends = [
        item["end_s"]
        for track in tracks.values()
        for item in track["items"]
        if item.get("end_s") is not None
    ]
    total_duration_s = max(all_ends) if all_ends else 35.0

    return {
        "cwd": str(cwd_path),
        "total_duration_s": total_duration_s,
        "tracks": tracks,
        "assets": _load_assets(cwd_path),
    }
