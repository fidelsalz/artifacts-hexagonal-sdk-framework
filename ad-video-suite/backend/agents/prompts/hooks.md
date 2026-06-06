# Hook Generator — Task Instructions

**On connect, check for existing work first:**
- If `hooks-index.md` exists in your cwd → **resume run**: read the index and all hook
  folders, then reply to the user with:
  - A brief recap of the hooks found (number, hook text, type per hook)
  - What refinements you can do: rewrite a specific hook, change its type, adjust word
    count to fit timing, or regenerate all 5 from scratch
  - Wait for instructions — do not regenerate anything automatically.
- Otherwise → **first run**: proceed below.

---

Your cwd is an arc folder (e.g. `A02R01/`). The folder name is the arc ID — derive it
from the last segment of your cwd path. Read all `.md` and `.json` files in your cwd for
context (arc brief, timing blueprint). Generate 5 scroll-stopping hook variants.

Hook folders are named `{arc}H{n:02d}` — e.g. if your cwd is `A02R01/`, create
`A02R01H01/`, `A02R01H02/`, … `A02R01H05/`. No campaign prefix.

For each hook create a folder directly in your cwd and inside it a document
`{arc}H{n:02d}.md` containing:
- Hook text (exact words, respecting the max_words from timing blueprint)
- Hook type (question / contradiction / bold claim / visual / statement)
- Why it stops the scroll
- Delivery note (pace, emphasis)

After creating all 5 hook folders, write `hooks-index.md` directly in your cwd:

| # | Folder | Hook Text | Type | Why It Stops the Scroll |
|---|--------|-----------|------|-------------------------|
| 1 | A02R01H01 | … | … | … |
…

<!-- Naming convention: {arc}H01/, {arc}H02/, … {arc}H05/ — index at {cwd}/hooks-index.md -->
