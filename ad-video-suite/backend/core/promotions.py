"""Promotion helpers: copy INT intelligence files into flat SCE or IMG folders."""
from __future__ import annotations

import re
import shutil
from pathlib import Path


_HOOK_RE     = re.compile(r'^A\d+R\d+H\d+$')
_ARC_RE      = re.compile(r'^(A\d+R\d+)H\d+$')
_ANGLE_RE    = re.compile(r'^(A\d+)R\d+$')
_ARC_ONLY_RE = re.compile(r'^(A\d+)(R\d+)$')


def promote_hook(campaign_dir: Path, hook_path: Path) -> dict:
    """Seed INT files for hook_path into SCE/{hook_id}/.

    hook_path must be an absolute path inside the campaign's INT/ tree whose
    last segment matches A##R##H##. The SCE destination is always a flat folder
    — all files land directly in SCE/{hook_id}/.

    Returns:
        {
            "sce_path": str,
            "files_copied":  [filename, ...],
            "files_skipped": [filename, ...],   # destination already existed
            "files_missing": [filename, ...],   # source not found
        }
    """
    hook_id = hook_path.name
    if not _HOOK_RE.match(hook_id):
        raise ValueError(f"Path last segment {hook_id!r} does not match A##R##H## pattern")

    arc_id   = _ARC_RE.match(hook_id).group(1)     # A02R01
    angle_id = _ANGLE_RE.match(arc_id).group(1)    # A02

    sources = {
        "research.md":           campaign_dir / "INT" / "research.md",
        f"{angle_id}.md":        campaign_dir / "INT" / angle_id / f"{angle_id}.md",
        f"{arc_id}.md":          campaign_dir / "INT" / angle_id / arc_id / f"{arc_id}.md",
        "timing-blueprint.json": campaign_dir / "INT" / angle_id / arc_id / "timing-blueprint.json",
        f"{hook_id}.md":         campaign_dir / "INT" / angle_id / arc_id / hook_id / f"{hook_id}.md",
    }

    dest_dir = campaign_dir / "SCE" / hook_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied, skipped, missing = [], [], []

    for filename, src in sources.items():
        dst = dest_dir / filename
        if not src.exists():
            missing.append(filename)
        elif dst.exists():
            skipped.append(filename)
        else:
            shutil.copy2(src, dst)
            copied.append(filename)

    return {
        "sce_path":      str(dest_dir),
        "files_copied":  copied,
        "files_skipped": skipped,
        "files_missing": missing,
    }


def promote_arc(campaign_dir: Path, arc_path: Path, platform: str) -> dict:
    """Seed INT files for arc_path into IMG/{platform}/.

    arc_path must be an absolute path inside the campaign's INT/ tree whose
    last segment matches A##R##. All files land flat in IMG/{platform}/.
    Hook brief files are discovered by enumerating A##R##H## subdirs.

    Returns:
        {
            "img_path":      str,
            "files_copied":  [filename, ...],
            "files_skipped": [filename, ...],
            "files_missing": [filename, ...],
        }
    """
    arc_id = arc_path.name
    m = _ARC_ONLY_RE.match(arc_id)
    if not m:
        raise ValueError(f"Path last segment {arc_id!r} does not match A##R## pattern")

    angle_id = m.group(1)  # e.g. A01

    sources: dict[str, Path] = {
        "research.md":    campaign_dir / "INT" / "research.md",
        f"{angle_id}.md": campaign_dir / "INT" / angle_id / f"{angle_id}.md",
        f"{arc_id}.md":   campaign_dir / "INT" / angle_id / arc_id / f"{arc_id}.md",
        "hooks-index.md": campaign_dir / "INT" / angle_id / arc_id / "hooks-index.md",
    }

    # Discover hook brief files by enumerating hook subdirs in the arc folder
    arc_dir = campaign_dir / "INT" / angle_id / arc_id
    if arc_dir.is_dir():
        for hook_dir in sorted(arc_dir.iterdir()):
            if hook_dir.is_dir() and _HOOK_RE.match(hook_dir.name):
                hook_file = hook_dir / f"{hook_dir.name}.md"
                sources[f"{hook_dir.name}.md"] = hook_file

    dest_dir = campaign_dir / "IMG" / platform / arc_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied, skipped, missing = [], [], []

    for filename, src in sources.items():
        dst = dest_dir / filename
        if not src.exists():
            missing.append(filename)
        elif dst.exists():
            skipped.append(filename)
        else:
            shutil.copy2(src, dst)
            copied.append(filename)

    return {
        "img_path":      str(dest_dir),
        "files_copied":  copied,
        "files_skipped": skipped,
        "files_missing": missing,
    }
