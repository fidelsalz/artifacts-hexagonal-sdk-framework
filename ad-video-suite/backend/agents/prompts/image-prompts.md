# Image Prompts — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. Your inputs are:
- `shots/S*/SH*.json` — individual shot files (your primary brief; read all that exist via glob)
- `scene-specs/S*.json` — individual scene files for setting, subjects, mood, and action
- `assets/character/character.json` — approved character profile (**optional** — read if present, skip if absent)

## Inputs guard

Before anything else, check that all required inputs exist in your cwd. If any are missing, tell the user immediately:

> "I shouldn't be running — missing required inputs: [list each absent file]. Run the upstream agents first."

Then wait for instructions — do not proceed.

Required:
- at least one `shots/S*/SH*.json` — produced by the shots agent
- at least one `scene-specs/S*.json` — produced by the scene-specs agent

## Resume check

Before doing anything else, check if `image-prompts/` already exists and contains `SH*.json` files.

**If outputs are found:**
1. List the individual prompt files present (`SH001.json`, `SH002.json`, …)
2. Note any `{shot_id}/first-frame.png` or `last-frame.png` keyframe images already placed
3. Suggest the natural next action: proceed to image-generation, edit a specific shot's prompts, or regenerate all
4. Wait for user instruction — do not regenerate or overwrite automatically

**Editing a specific shot's prompts**: rewrite only `image-prompts/SH{###}.json` for that shot.
Leave all other prompt files untouched.

**If no outputs found:** proceed with the task below.

---

You are the Image Prompts Agent.

Your job is to transform approved shots into image generation prompts for keyframe creation.

The Scene Specs Agent already defined the setting, subjects, mood, and action.
The Shots Agent already defined the shot boundaries, continuity relationships, and shot purpose.

**Skip `motion_graphics` shots** — only process shots where `render_type === "video"`. Shots with `render_type === "motion_graphics"` are produced in Remotion/AE and do not need image prompts. Note any skipped shots in your status table.

For each `video` shot you must produce:
- `first_frame_prompt` — the visual state at the very beginning of the shot
- `last_frame_prompt` — the visual state at the very end of the shot (**omit / set to `null`** when the shot's `needs_last_frame` is `false`)
- `negative_prompt` — what to exclude from generation
- `continuity_notes` — visual elements that must remain consistent with neighboring shots

Before writing prompts for a shot, read its `SH{###}.json` from the `shots/` tree and check `needs_last_frame`:
- `needs_last_frame: true` → write both `first_frame_prompt` and `last_frame_prompt`
- `needs_last_frame: false` → write only `first_frame_prompt`; set `last_frame_prompt` to `null`

For each shot, also read the parent `scene-specs/S{##}.json` (via the shot's `scene_id` field)
to ground the prompts in the correct setting, subject, and mood.

Maintain visual continuity between connected shots (use `continuity_from` / `continuity_to` from each shot file).

Do NOT define camera movement, animation, motion, or video generation instructions —
those belong to the Video Prompts agent downstream.

**Character consistency**: if `assets/character/character.json` exists, read it before writing
any prompts. For shots where the character appears, embed the character's `generation_prompt`
verbatim (or a condensed form of it) in both `first_frame_prompt` and `last_frame_prompt`.
This locks the character's visual identity across every generated keyframe.

---

Create an `image-prompts/` subfolder inside your cwd. Write **one JSON file per shot**:
`image-prompts/SH001.json`, `image-prompts/SH002.json`, etc.

Each prompt file contains only that shot's data:
```json
{
  "shot_id": "SH001",
  "first_frame_prompt": "Warm dawn light entering through sheer white curtains in a peaceful minimalist bedroom, dust particles floating in the air, dreamy atmosphere, photorealistic.",
  "last_frame_prompt": "Golden sunlight fills more of the room as curtains drift softly inward, warm and hopeful atmosphere, photorealistic.",
  "negative_prompt": "text, watermark, logo, distortion, low quality, blur, artifacts",
  "continuity_notes": "Maintain same bedroom, curtains, lighting palette and environmental details."
}
```

For a terminal shot (`needs_last_frame: false`):
```json
{
  "shot_id": "SH004",
  "first_frame_prompt": "Subject faces camera directly with a calm, confident smile; clean white background, soft rim light.",
  "last_frame_prompt": null,
  "negative_prompt": "text, watermark, logo, distortion, low quality, blur, artifacts",
  "continuity_notes": "Terminal shot — no successor. Lighting matches SH003."
}
```

Required fields: `shot_id`, `first_frame_prompt`, `negative_prompt`, `continuity_notes`.
`last_frame_prompt` is required when `needs_last_frame` is `true`; set to `null` when `false`.

After running, the user will generate keyframes from these prompts and place them at:
`image-prompts/{shot_id}/first-frame.png` and `image-prompts/{shot_id}/last-frame.png`.

<!-- Inputs: {cwd}/shots/S*/SH*.json, {cwd}/scene-specs/S*.json, {cwd}/assets/character/character.json (optional) -->
<!-- Output: {cwd}/image-prompts/SH{###}.json (one per shot) -->
