# Arc Generator — Task Instructions

**On connect, check for existing work first:**
- If `arcs-index.md` exists in your cwd → **resume run**: read the index and all arc
  folders, then reply to the user with:
  - A brief recap of the arcs found (number, names, emotional journey per arc)
  - What refinements you can do: rework a specific arc's pacing or tone, swap a phase,
    add a new variant, or regenerate all 3 from scratch
  - Wait for instructions — do not regenerate anything automatically.
- Otherwise → **first run**: proceed below.

---

Your cwd is an angle folder (e.g. `A02/`). The folder name is the angle ID — derive it
from the last segment of your cwd path. Read the `.md` file in your cwd for the angle brief.
Generate 3 emotional arc variants for this angle.

Arc folders are named `{angle}R{n:02d}` — e.g. if your cwd is `A02/`, create `A02R01/`,
`A02R02/`, `A02R03/`. No campaign prefix.

For each arc create a folder directly in your cwd and inside it a document `{angle}R{n:02d}.md`
containing:
- Arc name and emotional journey description
- Phase breakdown: hook → tension → release → CTA
- Tone and pacing notes
- Key visual mood per phase

After creating all 3 arc folders, write `arcs-index.md` directly in your cwd:

| # | Folder | Arc Name | Emotional Journey | Tone |
|---|--------|----------|-------------------|------|
| 1 | A02R01 | … | … | … |
…

<!-- Naming convention: {angle}R01/, {angle}R02/, {angle}R03/ — index at {cwd}/arcs-index.md -->
