# Graphics Plan — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. Your inputs are
`script/script.json` and `scene-specs/scene-specs.json`. Specify every Remotion
motion graphic needed.

Create a `graphics/` subfolder inside your cwd and write two files there:

`graphics/graphics-plan.json` — full version including captions:
- Array of graphics: { graphic_id, type, text, start_s, end_s, position,
  animation_in, animation_out, function, scene_id }

`graphics/no-captions-graphics-plan.json` — identical but with all entries where
`type === "caption"` removed.

`type`: "caption" | "lower-third" | "badge" | "cta" | "title"

<!-- Inputs: {cwd}/script/script.json, {cwd}/scene-specs/scene-specs.json -->
<!-- Output: {cwd}/graphics/graphics-plan.json, {cwd}/graphics/no-captions-graphics-plan.json -->
