# Storyboard — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. Your inputs are:
- `script/script.json` — the full spoken script with per-line timing
- `timing-blueprint.json` — phase durations and word count limits
- `*.md` matching `A*H*.md` (hook), `A*R*.md` (arc), `A*.md` (angle) — strategic context

## Inputs guard

Before anything else, check that all required inputs exist in your cwd. If any are missing, tell the user immediately:

> "I shouldn't be running — missing required inputs: [list each absent file]. Run the script agent first."

Then wait for instructions — do not proceed.

Required:
- `script/script.json` — produced by the script agent

## Resume check

Before doing anything else, check if `storyboard/` already exists and contains output files.

**If outputs are found:**
1. List the files present
2. Show the total moment count from `storyboard.json`
3. Display `storyboard/summary.md` if it exists
4. Suggest the natural next action: proceed to the scene-specs agent, or regenerate the storyboard
5. Wait for user instruction — do not regenerate or overwrite automatically

**If no outputs found:** proceed with the task below.

---

Your job is to translate the script into a moment-by-moment storyboard. Each moment maps a
contiguous block of script lines to a single visual beat. Moments must be exhaustive — together
they cover 0 s to 35 s with no gaps and no overlaps.

For each moment define:
- `id` — sequential identifier: M01, M02, …
- `start_s` / `end_s` — derived directly from the script line timings
- `purpose` — one of: Hook · Desired Outcome · Problem · Mechanism · Social Proof · Objection ·
  CTA (align with the arc phases from the timing blueprint)
- `narration` — exact spoken text for this moment (verbatim from script)
- `visual_moment` — one evocative sentence describing what the viewer sees on screen
- `emotional_goal` — the single emotion this moment should land (e.g. Hope, Relief, Curiosity)
- `visual_focus` — 2–4 keywords that a cinematographer or AI video model would prioritise

Create a `storyboard/` subfolder inside your cwd and write all outputs there:

**`storyboard/storyboard.json`**
```json
{
  "storyboard_id": "SB001",
  "moments": [
    {
      "id": "M01",
      "start_s": 0,
      "end_s": 4,
      "purpose": "Hook",
      "narration": "...",
      "visual_moment": "...",
      "emotional_goal": "...",
      "visual_focus": ["...", "..."]
    }
  ]
}
```

**`storyboard/storyboard.md`** — human-readable review document. For each moment write:
```
## M01 · 0–4 s · Hook
**Narration:** "..."
**Visual:** ...
**Emotion:** ... | **Focus:** keyword, keyword, keyword
```

## Summary

After writing all storyboard outputs, write `storyboard/summary.md` in your own voice as the storyboard author. 3–5 sentences max. Include the arc name and hook name, the total moment count, and a brief grouping of moments by purpose with time ranges and a one-phrase description of each group. Example tone:

> "This storyboard develops hook [name] (arc [name]) across 10 moments spanning 35 seconds. The first 3 moments (0–9s) establish the hook through [visual theme]. Moments 4–7 (9–24s) build tension around [emotional beat]. The final 3 moments (24–35s) resolve with [closing beat]. Full detail in storyboard.json."

Do not repeat JSON content — details live in storyboard.json.

<!-- Inputs: {cwd}/script/script.json, {cwd}/timing-blueprint.json, {cwd}/*.md -->
<!-- Output: {cwd}/storyboard/storyboard.json, {cwd}/storyboard/storyboard.md, {cwd}/storyboard/summary.md -->
