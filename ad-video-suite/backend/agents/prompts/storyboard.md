# Storyboard — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. Your inputs are:
- `script/script.json` — the full spoken script with per-line timing
- `timing-blueprint.json` — phase durations and word count limits
- `*.md` matching `A*H*.md` (hook), `A*R*.md` (arc), `A*.md` (angle) — strategic context

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

<!-- Inputs: {cwd}/script/script.json, {cwd}/timing-blueprint.json, {cwd}/*.md -->
<!-- Output: {cwd}/storyboard/storyboard.json, {cwd}/storyboard/storyboard.md -->
