# Narrative Concept Generator — Task Instructions

**On connect, check for existing work first:**
- If `arcs-index.md` exists in your cwd → **resume run**: read the index and all arc
  folders, then reply to the user with:
  - A brief recap of the narratives found (number, names, concept per narrative)
  - What refinements you can do: rework a specific narrative's beats, swap a scene,
    add a new variant, or regenerate all 3 from scratch
  - Wait for instructions — do not regenerate anything automatically.
- Otherwise → **first run**: proceed below.

---

Your cwd is an angle folder (e.g. `A02/`). The folder name is the angle ID — derive it
from the last segment of your cwd path. Read the `.md` file in your cwd for the angle brief.
Generate 3 narrative concept variants for this angle.

Arc folders are named `{angle}R{n:02d}` — e.g. if your cwd is `A02/`, create `A02R01/`,
`A02R02/`, `A02R03/`. No campaign prefix.

For each narrative create a folder directly in your cwd and inside it a document
`{angle}R{n:02d}.md` containing:

**Header**
- Narrative name and one-line concept statement
- Structural type (e.g. Before/After contrast, Journey, POV Demo, Problem/Solution reveal)

**Beat structure** — describe each beat as a named block:
- Beat name (e.g. "Opening State", "Product Moment", "Resolution", "CTA")
- **Physical manifestation**: one sentence describing the observable body action and posture
- **Facial expression**: specific cue (e.g. "furrowed brow, jaw slightly clenched", not "looks tired")
- **What the camera sees**: one sentence answering "what does the viewer actually watch?"
- Transition note to the next beat (brief — one line)

Keep beats to 3–5 per narrative. Prioritize clarity and visual specificity over abstraction.

**Fit note**
- Why this narrative fits the selected angle (one sentence)

After creating all 3 arc folders, write `arcs-index.md` directly in your cwd:

| # | Folder | Narrative Name | Concept | Structural Type |
|---|--------|----------------|---------|-----------------|
| 1 | A02R01 | … | … | … |
…

<!-- Naming convention: {angle}R01/, {angle}R02/, {angle}R03/ — index at {cwd}/arcs-index.md -->
