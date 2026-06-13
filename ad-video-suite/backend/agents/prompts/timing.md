# Timing Blueprint — Task Instructions

Your cwd is an arc folder (e.g. `A02R01/`). Read the `.md` file in your cwd for the
narrative concept. Allocate a 35-second timeline across the narrative beats.
If `{arc_id}-execution.md` is present, read it and apply its pacing style to phase durations
(conversational styles warrant longer tension pauses; tighter cut-driven styles compress mid-phases).

Write `timing-blueprint.json` directly in your cwd with:
- Array of phases: name, start_s, end_s, duration_s, max_words, mood
- Total must sum to exactly 35 seconds

<!-- Output: {cwd}/timing-blueprint.json -->
