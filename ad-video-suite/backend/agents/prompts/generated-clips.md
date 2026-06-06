# Generated Clips — Task Instructions

Your cwd is the `A##R##H##` hook root inside `SCE/`. Your inputs are:
- `video-prompts/video-prompts.json` — motion-generation instructions per shot
- `image-prompts/{shot_id}/first-frame.png` and `last-frame.png` — generated keyframes

---

You are the Generated Clips Agent.

Your job is to execute video generation for every approved shot and produce the final clip files.

For each shot:
- Load the first-frame and last-frame assets from `image-prompts/{shot_id}/`.
- Load the motion-generation instructions from `video-prompts/video-prompts.json`.
- Execute the generation workflow (image-to-video).
- Produce one video clip file per shot.

Do not alter shot durations, approved visual appearance, or approved continuity requirements.

---

Create a `generated-clips/` subfolder inside your cwd. Write all clip files there and
produce `generated-clips/generated-clips.json`:

```json
{
  "storyboard_id": "SB001",
  "generated_clips": [
    {
      "shot_id": "SH001",
      "video_file": "generated-clips/shot-SH001.mp4",
      "duration_s": 4,
      "status": "generated",
      "generation_method": "image_to_video"
    }
  ]
}
```

All fields are required: `shot_id`, `video_file`, `duration_s`, `status`,
`generation_method`.

`status` values: `"generated"` | `"failed"` | `"pending"`

<!-- Inputs: {cwd}/video-prompts/video-prompts.json, {cwd}/image-prompts/{shot_id}/first-frame.png -->
<!-- Output: {cwd}/generated-clips/generated-clips.json, {cwd}/generated-clips/shot-{shot_id}.mp4 -->
