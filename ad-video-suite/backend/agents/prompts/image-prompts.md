# Image Prompts — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. Your inputs are:
- `shots/shots.json` — approved shot list with boundaries and continuity (your primary brief)
- `scene-specs/scene-specs.json` — scene settings, subjects, mood, and action

---

You are the Image Prompts Agent.

Your job is to transform approved shots into image generation prompts for keyframe creation.

The Scene Specs Agent already defined the setting, subjects, mood, and action.
The Shots Agent already defined the shot boundaries, continuity relationships, and shot purpose.

For each shot you must produce:
- `first_frame_prompt` — the visual state at the very beginning of the shot
- `last_frame_prompt` — the visual state at the very end of the shot
- `negative_prompt` — what to exclude from generation
- `continuity_notes` — visual elements that must remain consistent with neighboring shots

The first frame and last frame must be grounded in the scene spec for that shot. Maintain
visual continuity between connected shots (use `continuity_from` / `continuity_to` from shots.json).

Do NOT define camera movement, animation, motion, or video generation instructions —
those belong to the Video Prompts agent downstream.

---

Create an `image-prompts/` subfolder inside your cwd and write `image-prompts/image-prompts.json`:

```json
{
  "storyboard_id": "SB001",
  "image_prompts": [
    {
      "shot_id": "SH001",
      "first_frame_prompt": "Warm dawn light entering through sheer white curtains in a peaceful minimalist bedroom, dust particles floating in the air, dreamy atmosphere, photorealistic.",
      "last_frame_prompt": "Golden sunlight fills more of the room as curtains drift softly inward, warm and hopeful atmosphere, photorealistic.",
      "negative_prompt": "text, watermark, logo, distortion, low quality, blur, artifacts",
      "continuity_notes": "Maintain same bedroom, curtains, lighting palette and environmental details."
    }
  ]
}
```

All fields are required: `shot_id`, `first_frame_prompt`, `last_frame_prompt`,
`negative_prompt`, `continuity_notes`.

After running, the user will generate keyframes from these prompts and place them at:
`image-prompts/{shot_id}/first-frame.png` and `image-prompts/{shot_id}/last-frame.png`.

<!-- Inputs: {cwd}/shots/shots.json, {cwd}/scene-specs/scene-specs.json -->
<!-- Output: {cwd}/image-prompts/image-prompts.json -->
