# Script Writer — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. It contains the INT input files seeded
at campaign scaffolding: `A*H*.md` (hook text), `A*R*.md` (arc), `A*.md` (angle),
`research.md` (audience context), and `timing-blueprint.json` (phase timing and word counts).

Line 1 of the script must be the exact hook text — never rewrite it.

Create a `script/` subfolder inside your cwd and write all outputs there:
- `script/script.json` — array of lines: { line_number, text, phase, start_s, end_s, word_count }
- `script/script-readthrough.md` — plain text, one line per entry, for quick human review
- `script/script.ssml` — for pasting into ElevenLabs TTS

<!-- Inputs: {cwd}/*.md, {cwd}/timing-blueprint.json -->
<!-- Output: {cwd}/script/script.json, {cwd}/script/script-readthrough.md, {cwd}/script/script.ssml -->
