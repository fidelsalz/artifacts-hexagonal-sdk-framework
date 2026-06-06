# Angle Generator — Task Instructions

**On connect, check for existing work first:**
- If `angles-index.md` exists in your cwd → **resume run**: read the index and all angle
  folders, then reply to the user with:
  - A brief recap of the angles found (number, names, one-line positioning per angle)
  - What refinements you can do: regenerate a specific angle, adjust tone/driver, add a
    new angle variant, or regenerate all 5 from scratch
  - Wait for instructions — do not regenerate anything automatically.
- Otherwise → **first run**: proceed below.

---

Your cwd is the `INT/` section folder. Read `research.md` from your cwd. Generate 5
distinct strategic positioning angles.

Angle folders are named `A01`, `A02`, … `A05` — no campaign prefix, no section prefix.

For each angle create a folder `A{n:02d}/` directly in your cwd and inside it a document
`A{n:02d}.md` containing:
- Angle name and one-line positioning statement
- Core emotional driver
- Target audience segment
- Primary message and proof point
- Why this angle beats the alternatives

After creating all 5 angle folders, write `angles-index.md` directly in your cwd:

| # | Folder | Angle Name | Positioning Statement | Emotional Driver |
|---|--------|------------|-----------------------|-----------------|
| 1 | A01 | … | … | … |
…

<!-- Naming convention: A01/, A02/, … A05/ — index at {cwd}/angles-index.md -->
