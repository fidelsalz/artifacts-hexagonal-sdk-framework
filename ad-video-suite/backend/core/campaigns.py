"""Campaign CRUD and folder scaffold.

A campaign is a directory under base_path named C### (auto-incremented).
At creation the app scaffolds:
  {slug}/
    campaign.json
    product/                    ← user drops product files here
    agents/
      agents-config.yaml        ← generated from template, fully resolved
      prompts/
        research.md ... etc.    ← stub prompt files copied from backend/agents/prompts/
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agents.config import (
    get_base_path,
    get_settings,
    resolve_campaign_config,
    save_settings,
)
from core.metrics import count_variations_generated

_STUB_PROMPTS_DIR = Path(__file__).parent.parent / "agents" / "prompts"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def update_settings(base_path: Optional[str] = None, max_active_campaigns: Optional[int] = None) -> dict:
    s = get_settings()
    if base_path is not None:
        s["base_path"] = base_path
    if max_active_campaigns is not None:
        s["max_active_campaigns"] = max_active_campaigns
    save_settings(s)
    return {
        "base_path":            s["base_path"],
        "max_active_campaigns": s.get("max_active_campaigns", 3),
    }


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _next_slug(base: Path) -> str:
    existing = []
    if base.exists():
        for d in base.iterdir():
            if d.is_dir() and re.match(r'^C\d{3}$', d.name):
                existing.append(int(d.name[1:]))
    next_num = max(existing, default=0) + 1
    return f"C{next_num:03d}"


# ---------------------------------------------------------------------------
# Campaign management
# ---------------------------------------------------------------------------

def list_campaigns() -> list[dict]:
    base = Path(get_base_path())
    if not base.exists():
        return []
    result = []
    for d in sorted(base.iterdir()):
        if not d.is_dir() or not re.match(r'^C\d{3}$', d.name):
            continue
        meta_file = d / "campaign.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text())
        meta["variations_generated"] = count_variations_generated(d)
        result.append(meta)
    return result


def get_campaign(slug: str) -> Optional[dict]:
    base = Path(get_base_path())
    d = base / slug
    meta_file = d / "campaign.json"
    if not d.exists() or not meta_file.exists():
        return None
    meta = json.loads(meta_file.read_text())
    meta["path"] = str(d)
    meta["variations_generated"] = count_variations_generated(d)
    return meta


def create_campaign(name: Optional[str] = None) -> dict:
    """Create a new campaign with auto-generated C### slug.

    Scaffolds:
      product/
      agents/
        agents-config.yaml   (fully resolved from template)
        prompts/             (stub .md files)
    """
    base = Path(get_base_path())
    slug = _next_slug(base)
    campaign_dir = base / slug

    # Core dirs
    (campaign_dir / "product").mkdir(parents=True, exist_ok=True)
    (campaign_dir / "agents" / "prompts").mkdir(parents=True, exist_ok=True)

    # Section folders
    for section in ("PRD", "IMG", "INT", "SCE"):
        (campaign_dir / section).mkdir(exist_ok=True)
    (campaign_dir / "PRD" / "images").mkdir(exist_ok=True)
    (campaign_dir / "IMG" / "ML").mkdir(exist_ok=True)

    # Per-campaign agents-config.yaml
    config_yaml = resolve_campaign_config(slug, str(base))
    (campaign_dir / "agents" / "agents-config.yaml").write_text(config_yaml, encoding="utf-8")

    # Stub prompt files
    if _STUB_PROMPTS_DIR.exists():
        for stub in _STUB_PROMPTS_DIR.glob("*.md"):
            dest = campaign_dir / "agents" / "prompts" / stub.name
            if not dest.exists():
                shutil.copy2(stub, dest)

    # Metadata
    meta = {
        "slug":       slug,
        "name":       name or slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "path":       str(campaign_dir),
    }
    (campaign_dir / "campaign.json").write_text(
        json.dumps({"slug": meta["slug"], "name": meta["name"], "created_at": meta["created_at"]}, indent=2)
    )
    return meta
