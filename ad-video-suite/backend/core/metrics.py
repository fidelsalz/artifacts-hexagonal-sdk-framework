"""Campaign filesystem metrics derived on demand from the folder tree."""
from __future__ import annotations

import re
from pathlib import Path

#_VARIATION_RE = re.compile(r'^A\d{3}R\d{3}H\d{3}$')
_VARIATION_RE = re.compile(r'^A\d+R\d+H\d+$')

def count_variations_generated(campaign_dir: Path) -> int:
    """Count hook folders (A###R###H###) anywhere under campaign_dir."""
    if not campaign_dir.exists():
        return 0
    return sum(
        1 for entry in campaign_dir.rglob("*")
        if entry.is_dir() and _VARIATION_RE.match(entry.name)
    )
