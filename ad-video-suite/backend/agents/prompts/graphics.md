# Graphics Plan — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. Your inputs are
`script/script.json`, `scene-specs/scene-specs.json`, and (if available) `shots/shots.json`.
Specify every Remotion motion graphic needed.

Two categories of graphics to plan:

1. **Overlay graphics** — captions, lower-thirds, badges, CTAs, titles. These appear on top of video shots (`render_type === "video"`) throughout the ad.
2. **Full motion graphic scenes** — scenes where `render_type === "motion_graphics"` in `scene-specs.json` (or `shots.json` if shots have been generated). These scenes are entirely produced in Remotion — no Higgsfield video exists for them. Specify the full visual composition for each: layout, animated elements, text, timing, and any data or product visuals needed.

## Inputs guard

Before anything else, check that all required inputs exist in your cwd. If any are missing, tell the user immediately:

> "I shouldn't be running — missing required inputs: [list each absent file]. Run the upstream agents first."

Then wait for instructions — do not proceed.

Required:
- `script/script.json` — produced by the script agent
- `scene-specs/scene-specs.json` — produced by the scene-specs agent

## Resume check

Before doing anything else, check if `graphics/` already exists and contains output files.

**If outputs are found:**
1. List the files present (`graphics-plan.json`, `no-captions-graphics-plan.json`)
2. Show the total graphic count from `graphics-plan.json`
3. Suggest the natural next action: review and proceed to Remotion composition, or regenerate the graphics plan
4. Wait for user instruction — do not regenerate or overwrite automatically

**If no outputs found:** proceed with the task below.

---

Create a `graphics/` subfolder inside your cwd and write two files there:

`graphics/graphics-plan.json` — full version including captions:
- Array of graphics: { graphic_id, type, text, start_s, end_s, position,
  animation_in, animation_out, function, scene_id }

`graphics/no-captions-graphics-plan.json` — identical but with all entries where
`type === "caption"` removed.

`type`: "caption" | "lower-third" | "badge" | "cta" | "title"

<!-- Inputs: {cwd}/script/script.json, {cwd}/scene-specs/scene-specs.json -->
<!-- Output: {cwd}/graphics/graphics-plan.json, {cwd}/graphics/no-captions-graphics-plan.json -->
