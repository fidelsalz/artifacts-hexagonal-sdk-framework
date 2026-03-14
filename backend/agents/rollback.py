"""Rollback utility — restores a coding directory from the latest tar.gz snapshot,
and provides a helper to clear an agent's out/ folder before a fresh run.

Snapshot naming convention:  {timestamp}-{foldername}.tar.gz
Snapshots live in the parent of coding_dir (i.e. backend/src/).
The archive root matches the folder name (e.g. ports/ inside ports.tar.gz).

Usage:
    for event in rollback_coding_dir(cfg.coding_dir):
        yield event
"""
import glob
import shutil
import tarfile
from pathlib import Path


def rollback_coding_dir(coding_dir: str) -> list[dict]:
    """Wipe coding_dir and restore it from the latest *-{name}.tar.gz snapshot.

    Returns a list of SSE-ready status dicts to stream to the frontend.
    """
    events: list[dict] = []
    coding_path = Path(coding_dir)
    src_dir     = coding_path.parent
    folder_name = coding_path.name

    # Locate snapshots matching *-{foldername}.tar.gz in the parent dir
    matches = sorted(src_dir.glob(f"*-{folder_name}.tar.gz"))

    if not matches:
        events.append({"type": "status", "message": f"No snapshot found for '{folder_name}' — skipping rollback."})
        return events

    snapshot = matches[-1]   # latest by lexicographic sort (timestamp prefix)
    events.append({"type": "status", "message": f"Rollback: unpacking {snapshot.name} ..."})

    # Remove current directory contents
    if coding_path.exists():
        shutil.rmtree(coding_path)

    # Extract into src_dir — archive root is folder_name/ so result is src_dir/folder_name/
    with tarfile.open(snapshot, "r:gz") as tar:
        tar.extractall(path=src_dir)

    events.append({"type": "status", "message": f"Rollback complete → {folder_name}/"})
    return events


def clear_out_dir(cwd: str) -> list[dict]:
    """Delete all contents of {cwd}/out/ without removing the folder itself."""
    out_path = Path(cwd) / "out"
    if not out_path.exists():
        return [{"type": "status", "message": f"out/ not found at {cwd}, skipping."}]

    removed = 0
    for item in out_path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        removed += 1

    return [{"type": "status", "message": f"Cleared out/ ({removed} items removed)."}]
