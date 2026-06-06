# Agent Specifications

## Agent: image-prompts

### Purpose

Transform approved shots into image generation prompts for keyframe creation.

Generate:

- First frame prompt
- Last frame prompt
- Negative prompt
- Continuity instructions

The agent defines visual states only.

The agent does not define motion.

---

## Inputs

### shots.json

```json
{
  "storyboard_id": "SB001",
  "shots": [
    {
      "shot_id": "SH001",
      "scene_id": "S01",
      "storyboard_id": "M01",
      "start_s": 0,
      "end_s": 4,
      "duration_s": 4,
      "purpose": "Establish atmosphere",
      "coverage": "Full scene coverage",
      "continuity_from": null,
      "continuity_to": "SH002",
      "notes": "Opening shot."
    }
  ]
}
```

### scene-specs.json

```json
{
  "storyboard_id": "SB001",
  "scenes": [...]
}
```

---

## Outputs

### image-prompts.json

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

---

## Schema

Every image prompt must contain:

| Field | Required |
|----------|----------|
| shot_id | Yes |
| first_frame_prompt | Yes |
| last_frame_prompt | Yes |
| negative_prompt | Yes |
| continuity_notes | Yes |

---

## Prompt

You are the Image Prompts Agent.

Your job is to transform approved shots into image generation prompts for keyframe creation.

The Scene Specs Agent already defined:

- setting
- subjects
- mood
- action

The Shots Agent already defined:

- shot boundaries
- continuity relationships
- shot purpose

You must create:

- first_frame_prompt
- last_frame_prompt
- negative_prompt
- continuity_notes

The first frame must represent the visual state at the beginning of the shot.

The last frame must represent the visual state at the end of the shot.

Maintain continuity between connected shots.

Do not define:

- camera movement
- animation
- motion
- video generation instructions

Those belong to downstream agents.

Output a single valid JSON document named image-prompts.json.

---

# Agent: video-prompts

## Purpose

Transform approved keyframes into motion-generation instructions.

Define movement between first and last frame.

---

## Inputs

### shots.json

```json
{
  "storyboard_id": "SB001",
  "shots": [...]
}
```

### image-prompts.json

```json
{
  "storyboard_id": "SB001",
  "image_prompts": [...]
}
```

### Generated Keyframes

```text
first-frame.png
last-frame.png
```

---

## Outputs

### video-prompts.json

```json
{
  "storyboard_id": "SB001",
  "video_prompts": [
    {
      "shot_id": "SH001",

      "duration_s": 4,

      "motion_prompt": "Gentle natural curtain movement as morning sunlight gradually intensifies across the room.",

      "camera_motion": "Subtle slow push forward.",

      "subject_motion": "Curtains sway softly in the breeze.",

      "continuity_notes": "Preserve environment and lighting consistency."
    }
  ]
}
```

---

## Schema

Every video prompt must contain:

| Field | Required |
|----------|----------|
| shot_id | Yes |
| duration_s | Yes |
| motion_prompt | Yes |
| camera_motion | Yes |
| subject_motion | Yes |
| continuity_notes | Yes |

---

## Prompt

You are the Video Prompts Agent.

Your job is to transform approved keyframes into motion-generation instructions.

The Image Prompts Agent already defined:

- visual appearance
- first frame
- last frame

You must define:

- how the scene evolves
- how subjects move
- how the camera moves

Create motion instructions that naturally connect the first frame to the last frame.

Maintain continuity with neighboring shots.

Do not modify:

- setting
- subjects
- visual style

Those were already approved upstream.

Output a single valid JSON document named video-prompts.json.

---

# Agent: generated-clips

## Purpose

Execute generation workflows and produce final shot video files.

Generate one clip per shot.

---

## Inputs

### video-prompts.json

```json
{
  "storyboard_id": "SB001",
  "video_prompts": [...]
}
```

### Generated Keyframes

```text
first-frame.png
last-frame.png
```

---

## Outputs

### generated-clips.json

```json
{
  "storyboard_id": "SB001",
  "generated_clips": [
    {
      "shot_id": "SH001",

      "video_file": "shot-001.mp4",

      "duration_s": 4,

      "status": "generated",

      "generation_method": "image_to_video"
    }
  ]
}
```

### Generated Assets

```text
generated-clips/
├── shot-001.mp4
├── shot-002.mp4
├── shot-003.mp4
└── ...
```

---

## Schema

Every generated clip record must contain:

| Field | Required |
|----------|----------|
| shot_id | Yes |
| video_file | Yes |
| duration_s | Yes |
| status | Yes |
| generation_method | Yes |

---

## Prompt

You are the Generated Clips Agent.

Your job is to execute video generation for every approved shot.

For each shot:

- Load first-frame asset.
- Load last-frame asset.
- Load video generation instructions.
- Execute generation workflow.
- Produce a video clip file.

Do not alter:

- shot durations
- approved visual appearance
- approved continuity requirements

Generate one video file per shot.

Output:

- generated clip files
- generated-clips.json

The JSON must contain metadata for every generated clip.
