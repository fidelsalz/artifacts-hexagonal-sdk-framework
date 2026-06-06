"""Migrate an existing campaign from the old C###A##R##H## convention to the new
section-based INT/A##/A##R##/A##R##H## convention.

Usage:
    python migrate_to_sections.py /path/to/campaigns/C001

What it does:
  1. Creates C001/INT/ and C001/SCE/
  2. Moves research.md (if present) into INT/
  3. For each angle folder (C001A01/):
       a. Moves it to INT/A01/
       b. Walks all nested content and strips the C001 prefix from every
          folder and file name (C001A01R01/ → A01R01/, C001A01R01.md → A01R01.md, etc.)
  4. Updates cwd_pattern values in agents/agents-config.yaml

Dry-run mode (no changes made):
    python migrate_to_sections.py /path/to/campaigns/C001 --dry-run
"""
import re
import shutil
import sys
from pathlib import Path

_ANGLE_RE = re.compile(r'^C\d{3}A\d+$')
_SLUG_PREFIX_RE = re.compile(r'^C\d{3}')

# Longest first so shorter patterns don't corrupt longer ones during YAML patch
_OLD_YAML_PATTERNS = [
    (r"C\d{3}A\d+R\d+H\d+$",  r"A\d+R\d+H\d+$"),
    (r"C\d{3}A\d+R\d+$",      r"A\d+R\d+$"),
    (r"C\d{3}A\d+$",          r"A\d+$"),
    (r"C\d{3}$",              r"[A-Z]{3}$"),
]


def _strip_slug(name: str, slug: str) -> str:
    """Remove leading campaign slug from a name: C001A01R01 → A01R01."""
    if name.startswith(slug):
        return name[len(slug):]
    return name


def _rename_contents(folder: Path, slug: str, dry_run: bool, base: Path) -> None:
    """Bottom-up walk: rename every file/folder inside `folder` that starts with slug."""
    # Walk bottom-up so children are renamed before parents
    for item in sorted(folder.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if item.name.startswith(slug):
            new_name = _strip_slug(item.name, slug)
            new_path = item.parent / new_name
            print(f"  ren  {item.relative_to(base)}  →  {new_path.relative_to(base)}")
            if not dry_run:
                item.rename(new_path)


def migrate(campaign_dir: Path, dry_run: bool) -> None:
    if not campaign_dir.exists():
        print(f"ERROR: {campaign_dir} does not exist")
        sys.exit(1)

    slug = campaign_dir.name
    if not re.match(r'^C\d{3}$', slug):
        print(f"ERROR: {slug!r} does not look like a campaign slug (C###)")
        sys.exit(1)

    def mv(src: Path, dst: Path) -> None:
        print(f"  mv   {src.relative_to(campaign_dir)}  →  {dst.relative_to(campaign_dir)}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

    def mkdir(path: Path) -> None:
        print(f"  mkdir {path.relative_to(campaign_dir)}")
        if not dry_run:
            path.mkdir(parents=True, exist_ok=True)

    # 1 — section folders
    mkdir(campaign_dir / "INT")
    mkdir(campaign_dir / "SCE")

    # 2 — research.md
    research = campaign_dir / "research.md"
    if research.exists():
        mv(research, campaign_dir / "INT" / "research.md")

    # 3 — angle folders (arcs and hooks are nested inside, move with parent)
    angle_folders = sorted(
        p for p in campaign_dir.iterdir()
        if p.is_dir() and _ANGLE_RE.match(p.name)
    )

    for src in angle_folders:
        short_name = _strip_slug(src.name, slug)          # C001A01 → A01
        dst = campaign_dir / "INT" / short_name
        mv(src, dst)
        # Now rename all nested C001... items inside the moved folder
        target = dst if not dry_run else src               # in dry-run src hasn't moved
        _rename_contents(target, slug, dry_run, campaign_dir)

    # Clean up any remaining slug-prefixed items already under INT
    # (handles partially-migrated campaigns where angles were moved but not renamed)
    int_dir = campaign_dir / "INT"
    if int_dir.exists():
        _rename_contents(int_dir, slug, dry_run, campaign_dir)

    # 4 — patch agents-config.yaml
    config_yaml = campaign_dir / "agents" / "agents-config.yaml"
    if config_yaml.exists():
        print(f"  patch {config_yaml.relative_to(campaign_dir)}")
        if not dry_run:
            text = config_yaml.read_text()
            for old, new in _OLD_YAML_PATTERNS:
                text = text.replace(old, new)
            # Add sections: [INT] after each agent's Glob tool entry (idempotent)
            import re as _re
            text = _re.sub(
                r'(      - Glob\n)(?!      sections:)',
                r'\1      sections: [INT]\n',
                text,
            )
            config_yaml.write_text(text)
    else:
        print(f"  WARN: {config_yaml} not found — skipping config patch")

    print()
    print("Dry run complete — no files were changed." if dry_run else "Migration complete.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv

    if not args:
        print(__doc__)
        sys.exit(1)

    migrate(Path(args[0]).resolve(), dry_run)
