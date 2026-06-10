import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

log = logging.getLogger(__name__)

router = APIRouter()

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _load_assets(cwd: Path) -> dict:
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
        else:
            files = sorted(str(p) for p in subdir.rglob("*") if p.is_file())
            result[name] = {"available": bool(files), "files": files}
    return result


def _load_concepts(cwd: Path) -> list:
    concepts_path = cwd / "ad_concepts.json"
    try:
        raw = _read_json(concepts_path)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    ads_dir = cwd / "ads"
    prompts_dir = cwd / "prompts"
    result = []

    for concept in raw:
        cid = concept.get("id")

        # Find generated image: ads/ad-ml-{id}-*.png
        image = None
        if ads_dir.is_dir() and cid is not None:
            matches = sorted(ads_dir.glob(f"ad-ml-{cid}-*"))
            image = str(matches[0]) if matches else None

        # Find prompt file: prompts/ad_{id}.md
        prompt_file = None
        if prompts_dir.is_dir() and cid is not None:
            p = prompts_dir / f"ad_{cid}.md"
            prompt_file = str(p) if p.is_file() else None

        # Status
        if image:
            status = "generated"
        elif prompt_file:
            status = "prompted"
        else:
            status = "pending"

        result.append({
            "id": cid,
            "concept": concept.get("concept"),
            "hook": concept.get("hook"),
            "hook_type": concept.get("hook_type"),
            "audience": concept.get("audience"),
            "angle": concept.get("angle"),
            "headline_ptbr": concept.get("headline_ptbr"),
            "format": concept.get("format"),
            "recommended_model": concept.get("recommended_model"),
            "visual_approach": concept.get("visual_approach"),
            "status": status,
            "image": image,
            "prompt_file": prompt_file,
        })

    return result


def _infer_platform(cwd: Path) -> str:
    # IMG/ML/A01R03 → cwd.parent is IMG/ML, cwd.parent.name is ML
    return cwd.parent.name if cwd.parent.name not in ("IMG", "") else "unknown"


@router.get("/api/img-ads")
async def get_img_ads(cwd: str = Query(...)):
    """Return ad concepts and generated images for an IMG platform arc folder.

    Reads ad_concepts.json, matches each concept to its generated image in ads/
    and prompt file in prompts/, and returns available assets.
    """
    cwd_path = Path(cwd).resolve()
    if not cwd_path.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {cwd}")

    return {
        "cwd": str(cwd_path),
        "platform": _infer_platform(cwd_path),
        "concepts": _load_concepts(cwd_path),
        "assets": _load_assets(cwd_path),
    }
