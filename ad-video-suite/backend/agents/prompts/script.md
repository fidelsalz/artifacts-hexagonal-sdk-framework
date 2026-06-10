# Script Writer — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. It contains the INT input files seeded
at campaign scaffolding: `A*H*.md` (hook text), `A*R*.md` (arc), `A*.md` (angle),
`research.md` (audience context), and `timing-blueprint.json` (phase timing and word counts).

## Inputs guard

Before anything else, check that all required inputs exist in your cwd. If any are missing, tell the user immediately:

> "I shouldn't be running — missing required inputs: [list each absent file]. Run promote-hook on this hook folder first."

Then wait for instructions — do not proceed.

Required:
- `timing-blueprint.json` — seeded by promote-hook
- at least one `A*H*.md` hook file — seeded by promote-hook

## Resume check

Before doing anything else, check if `script/` already exists and contains output files.

**If outputs are found:**
1. List the files present (`script-blueprint.json`, `script.json`, `script-readthrough.md`, `script-blueprint.ssml`)
2. Show the total line count and word count from `script-blueprint.json`
3. Suggest the natural next action: proceed to the storyboard agent, or regenerate the script
4. Wait for user instruction — do not regenerate or overwrite automatically

**If no outputs found:** proceed with the task below.

---

Line 1 of the script must be the exact hook text — never rewrite it.

Create a `script/` subfolder inside your cwd and write all outputs there:
- `script/script-blueprint.json` — array of lines: `{ line_number, text, phase, start_s, end_s, word_count }`. These timings are estimates based on the timing blueprint.
- `script/script.json` — an exact copy of `script-blueprint.json`. This file will be overwritten by the backend with real audio timing if an SRT file is later dropped in `script/`. Writing it here ensures it exists for downstream agents.
- `script/script-readthrough.md` — plain text, one line per entry, for quick human review
- `script/script-blueprint.ssml` — for pasting into ElevenLabs TTS to generate the audio file

<!-- Inputs: {cwd}/*.md, {cwd}/timing-blueprint.json -->
<!-- Output: {cwd}/script/script-blueprint.json, {cwd}/script/script.json, {cwd}/script/script-readthrough.md, {cwd}/script/script-blueprint.ssml -->
