# Ad Video Suite — Backend API Reference

Base URL: `http://localhost:8011`

All request/response bodies are JSON. All file paths in query params and bodies are **absolute filesystem paths**.

---

## Settings

### `GET /api/settings`
Returns the current server settings.

**Response**
```json
{
  "base_path": "/absolute/path/to/campaigns",
  "max_active_campaigns": 3
}
```

---

### `PUT /api/settings`
Update server settings. Fields are optional — omit to leave unchanged.

**Body**
```json
{
  "base_path": "/absolute/path/to/campaigns",
  "max_active_campaigns": 3
}
```

**Response** — updated settings object (same shape as GET).

---

## Campaigns

### `GET /api/campaigns`
List all campaigns found in `base_path`.

**Response**
```json
[
  { "slug": "C001", "name": "My Campaign", "path": "/campaigns/C001" }
]
```

---

### `POST /api/campaigns`
Create a new campaign. Slug is auto-generated (`C001`, `C002`, …). Scaffolds `PRD/`, `PRD/images/`, `IMG/`, `IMG/ML/`, `INT/`, `SCE/`.

**Body** *(name is optional)*
```json
{ "name": "My Campaign" }
```

**Response**
```json
{ "slug": "C001", "name": "My Campaign", "path": "/campaigns/C001" }
```

---

### `GET /api/campaigns/{slug}`
Get metadata for a single campaign.

**Response**
```json
{ "slug": "C001", "name": "My Campaign", "path": "/campaigns/C001" }
```

**Errors** — `404` if the slug doesn't exist.

---

## Campaign Tree

### `GET /api/tree`
Return the full folder tree for all campaigns. Each node lists agents available at that folder and their status.

**Response**
```json
[
  {
    "name": "C001",
    "path": "/campaigns/C001",
    "available_agents": ["product-creator"],
    "children": [
      {
        "name": "INT",
        "path": "/campaigns/C001/INT",
        "available_agents": [
          { "id": "research", "status": "ready",     "blocked_by": [] },
          { "id": "angles",   "status": "blocked",   "blocked_by": ["research.md"] }
        ],
        "children": [...]
      }
    ]
  }
]
```

**Note**: `available_agents` at the campaign root is a `string[]` (agent IDs only). At every child node it is `{id, status, blocked_by}[]` with full status. This asymmetry is intentional — root-level agents rarely have blocking inputs.

`status` values: `"ready"` | `"completed"` | `"blocked"`.  
`blocked_by` lists the relative paths of missing required inputs.

---

## Agents

### `GET /api/agents?campaign={slug}`
List all agents defined for a campaign (or the template if `campaign` is omitted).

**Response**
```json
[
  {
    "id": "script",
    "name": "Script Writer",
    "role": "...",
    "comm_type": "ws",
    "cwd_pattern": "A\\d+R\\d+H\\d+$"
  }
]
```

---

### `GET /api/agents/{agent_name}/config?campaign={slug}`
Get full config for a single agent.

**Response**
```json
{
  "id": "script",
  "name": "Script Writer",
  "role": "...",
  "comm_type": "ws",
  "cwd_pattern": "A\\d+R\\d+H\\d+$",
  "model": "claude-opus-4-5"
}
```

**Errors** — `404` if agent not found.

---

### `GET /api/infer-agent?path={abs_path}&campaign={slug}`
Return agents whose `cwd_pattern` matches the last segment of `path`, filtered by section, with current status.

**Response**
```json
[
  {
    "id": "script",
    "name": "Script Writer",
    "role": "...",
    "status": "ready",
    "blocked_by": []
  }
]
```

---

### `POST /api/launch`
Resolve a folder path to a launchable agent and return the WebSocket URL.

If `agent_id` is omitted and exactly one agent matches, it is auto-selected.  
If multiple agents match and `agent_id` is omitted, returns `ambiguous: true` — the UI should show a picker and re-call with `agent_id` set.

**Body**
```json
{
  "path": "/campaigns/C001/SCE/A01R01H01",
  "agent_id": "script"
}
```

**Unambiguous response**
```json
{
  "ambiguous": false,
  "agent_id": "script",
  "agent_name": "Script Writer",
  "role": "...",
  "campaign": "C001",
  "cwd": "/campaigns/C001/SCE/A01R01H01",
  "status": "ready",
  "ws_url": "/ws/agents/script/chat?cwd=...&campaign=C001"
}
```

**Ambiguous response**
```json
{
  "ambiguous": true,
  "campaign": "C001",
  "cwd": "/campaigns/C001/INT/A01/A01R01",
  "candidates": [
    { "id": "timing",    "name": "Timing Blueprint", "role": "...", "status": "ready" },
    { "id": "hooks",     "name": "Hook Generator",   "role": "...", "status": "blocked" },
    { "id": "character", "name": "Character",        "role": "...", "status": "ready" }
  ]
}
```

**Errors** — `400` if path doesn't exist, no agent matches, or `agent_id` doesn't fit the folder.

---

### `GET /api/sessions`
List active WebSocket sessions grouped by campaign.

**Response**
```json
{
  "active_campaigns": ["C001"],
  "sessions": {
    "C001": ["script", "storyboard"]
  }
}
```

---

## WebSocket — Agent Chat

### `WS /ws/agents/{agent_name}/chat?cwd={abs_path}&campaign={slug}`

Opens a persistent multi-turn session. The agent runs its opening task immediately on connect, then waits for follow-up messages.

**Client → Server messages**

| `type` | Fields | Description |
|--------|--------|-------------|
| `message` | `text: string` | Send a follow-up message to the agent |
| `interrupt` | — | Interrupt the current generation |
| `new_session` | — | Reset and re-run the opening task |

**Server → Client events**

| `type` | Fields | Description |
|--------|--------|-------------|
| `connected` | `agent`, `cwd` | Session established |
| `assistant` | `text` | Streamed text chunk from the agent |
| `result` | varies | Tool use result or structured output |
| `turn_complete` | — | Agent finished its current turn |
| `interrupted` | — | Generation was interrupted |
| `session_reset` | — | Session was reset via `new_session` |
| `error` | `message` | Error — connection closes after this |

**Pre-check**: if the agent's required inputs are missing (`status: "blocked"`), the server sends an `error` event and closes immediately.

---

## Promotions

### `POST /api/promote-hook`
Seed a `SCE/{hook_id}/` folder from an INT hook folder. Copies context files and `assets/character/` (if present). Idempotent — files already at the destination are skipped.

**Body**
```json
{ "path": "/campaigns/C001/INT/A01/A01R01/A01R01H01" }
```

Files copied: `research.md`, `A01.md`, `A01R01.md`, `timing-blueprint.json`, `A01R01H01.md`, `assets/character/`.

**Response**
```json
{
  "sce_path": "/campaigns/C001/SCE/A01R01H01",
  "files_copied":  ["research.md", "A01.md", "A01R01.md", "timing-blueprint.json", "A01R01H01.md", "assets/character/"],
  "files_skipped": [],
  "files_missing": []
}
```

**Errors** — `400` if path doesn't exist or last segment doesn't match `A##R##H##`.

---

### `POST /api/promote-arc`
Seed an `IMG/{platform}/{arc_id}/` folder from an INT arc folder. Copies context files (including all hook briefs found in the arc) and `assets/character/`. Idempotent.

**Body**
```json
{
  "path": "/campaigns/C001/INT/A01/A01R01",
  "platform": "ML"
}
```

`platform` must be 2–3 uppercase letters (e.g. `"ML"`, `"FB"`).

Files copied: `research.md`, `A01.md`, `A01R01.md`, `hooks-index.md`, one `A01R01H##.md` per hook found, `assets/character/`.

**Response**
```json
{
  "img_path": "/campaigns/C001/IMG/ML/A01R01",
  "files_copied":  ["research.md", "A01.md", "A01R01.md", "hooks-index.md", "A01R01H01.md", "assets/character/"],
  "files_skipped": [],
  "files_missing": []
}
```

**Errors** — `400` if path doesn't exist, last segment doesn't match `A##R##`, or `platform` is invalid.

---

## Files

### `GET /api/files/list?path={abs_path}`
List the contents of a directory.

**Response**
```json
{
  "path": "/campaigns/C001/SCE/A01R01H01",
  "entries": [
    { "name": "script",     "type": "dir",  "path": "/campaigns/C001/SCE/A01R01H01/script" },
    { "name": "shots",      "type": "dir",  "path": "/campaigns/C001/SCE/A01R01H01/shots" },
    { "name": "summary.md", "type": "file", "path": "/campaigns/C001/SCE/A01R01H01/summary.md" }
  ]
}
```

---

### `GET /api/files/read?path={abs_path}`
Read a file as UTF-8 text.

**Response**
```json
{ "path": "/absolute/path/file.json", "content": "..." }
```

---

### `GET /api/files/serve?path={abs_path}&download={bool}`
Serve a file with its correct MIME type. Use for images (`image/png`, `image/jpeg`, `image/webp`) and videos (`video/mp4`).

- `download=false` (default) — `Content-Disposition: inline` (display in browser)
- `download=true` — `Content-Disposition: attachment` (force download)

All absolute image/video paths returned by the timeline and img-ads endpoints can be passed directly to this endpoint.

---

### `POST /api/files/write`
Write text content to a file. Parent directory must exist.

**Body**
```json
{ "path": "/absolute/path/file.md", "content": "..." }
```

**Response**
```json
{ "ok": true }
```

---

## Timeline

### `GET /api/timeline?cwd={abs_path}`

Return all time-positioned artifact tracks plus available assets for a SCE hook root folder (`SCE/A##R##H##/`). Each track reads its corresponding JSON file; if the file is missing or malformed the track returns `available: false` with an empty items array — no error.

**Response**
```json
{
  "cwd": "/campaigns/C001/SCE/A01R01H01",
  "total_duration_s": 35.0,
  "tracks": {
    "script": {
      "available": true,
      "items": [
        {
          "id": "L01",
          "start_s": 0.0,
          "end_s": 3.0,
          "label": "spoken line text",
          "phase": "Hook"
        }
      ]
    },
    "storyboard": {
      "available": true,
      "items": [
        {
          "id": "M01",
          "start_s": 0.0,
          "end_s": 5.0,
          "label": "visual moment description",
          "purpose": "Hook"
        }
      ]
    },
    "scene_specs": {
      "available": true,
      "items": [
        {
          "id": "S01",
          "start_s": 0.0,
          "end_s": 5.0,
          "label": "subject description",
          "purpose": "Hook",
          "mood": "tense"
        }
      ]
    },
    "shots": {
      "available": true,
      "items": [
        {
          "id": "SH001",
          "start_s": 0.0,
          "end_s": 3.0,
          "label": "coverage description",
          "purpose": "Hook",
          "gen_status": "imaged",
          "files": {
            "image_generation": {
              "approved": [
                {
                  "attempt": "001",
                  "model": "nano_banana_pro",
                  "first_frame_job_id": "higgsfield-job-id-abc",
                  "last_frame_job_id": "higgsfield-job-id-def",
                  "character_reference_job_id": null,
                  "first_frame": "/campaigns/C001/SCE/A01R01H01/image-generation/SH001/approved/attempt-001-first-frame.png",
                  "last_frame": "/campaigns/C001/SCE/A01R01H01/image-generation/SH001/approved/attempt-001-last-frame.png"
                }
              ],
              "attempts_count": 1
            },
            "video_url": null
          }
        }
      ]
    },
    "graphics": {
      "available": true,
      "items": [
        {
          "id": "g01",
          "start_s": 0.0,
          "end_s": 2.5,
          "label": "caption text",
          "type": "caption"
        }
      ]
    }
  },
  "assets": {
    "character": {
      "available": true,
      "higgsfield_job_id": "higgsfield-job-id-xyz",
      "generation_prompt": "Brazilian woman, 30s, confident smile...",
      "approved_image": "/campaigns/C001/SCE/A01R01H01/assets/character/approved/approved.png",
      "character_json": "/campaigns/C001/SCE/A01R01H01/assets/character/character.json"
    },
    "product": {
      "available": true,
      "files": [
        "/campaigns/C001/SCE/A01R01H01/assets/product/product-reference.jpg"
      ]
    }
  }
}
```

**Track sources**

| Track | JSON file (relative to `cwd`) | Format |
|---|---|---|
| `script` | `script/script.json` | flat array of line objects |
| `storyboard` | `storyboard/storyboard.json` | `moments[]` in a dict |
| `scene_specs` | `scene-specs/scene-specs.json` | `scenes[]` in a dict |
| `shots` | `shots/shots.json` | `shots[]` in a dict |
| `graphics` | `graphics/graphics-plan.json` | `graphics[]` in a dict |

**`total_duration_s`** — derived from the highest `end_s` across all tracks; defaults to `35.0` if no items have timing.

**Shot `gen_status` values** (progressive — highest matching level wins)

| Value | Meaning |
|---|---|
| `pending` | `image-generation/{shot_id}/` not scaffolded yet |
| `prompted` | `image-generation/{shot_id}/` exists but no approved frames |
| `imaged` | Approved attempt(s) in `image-generation/{shot_id}/approved/` |
| `video_prompted` | Approved video prompt in `video-prompts/{shot_id}/approved/` |
| `generated` | Approved clip in `generated-clips/{shot_id}/approved/` — `video_url` is set |

**Shot `files.image_generation`**  
Each approved attempt includes `first_frame` and `last_frame` — absolute paths to downloaded PNGs in `image-generation/{shot_id}/approved/` (naming: `attempt-001-first-frame.png`). Pass to `GET /api/files/serve` to display. `first_frame_job_id` / `last_frame_job_id` are the originating Higgsfield job IDs. `attempts_count` counts all JSON files across `attempts/`, `approved/`, and `disapproved/`.

**`assets` object**  
Keyed by subfolder name under `assets/`. Empty object `{}` if `assets/` doesn't exist.

- **`character`** — `higgsfield_job_id` can be passed as reference media to Higgsfield generation calls. `approved_image` is a local path servable via `GET /api/files/serve`.
- **Other subfolders** (e.g. `product`) — `files[]` lists all local paths, also servable via `GET /api/files/serve`.

**Errors** — `400` if `cwd` does not exist.

---

## IMG Ads

### `GET /api/img-ads?cwd={abs_path}`

Return ad concepts and generated images for an `IMG/{platform}/{arc_id}/` folder. No time axis — each concept is an independent image ad for the arc.

**Response**
```json
{
  "cwd": "/campaigns/C001/IMG/ML/A01R03",
  "platform": "ML",
  "concepts": [
    {
      "id": 1,
      "concept": "Golden Hour Focus",
      "hook": "A01R03H01",
      "hook_type": "Question",
      "audience": "Professionals 30–45",
      "angle": "Pure aspiration — the energized day they want to have",
      "headline_ptbr": "E se você pudesse terminar o dia com a mesma energia com que começou?",
      "format": "1:1",
      "recommended_model": "GPT Image",
      "visual_approach": "Lifestyle scene — person at a golden-hour desk…",
      "status": "generated",
      "image": "/campaigns/C001/IMG/ML/A01R03/ads/ad-ml-1-golden-hour-focus.png",
      "prompt_file": "/campaigns/C001/IMG/ML/A01R03/prompts/ad_1.md"
    }
  ],
  "assets": {
    "character": {
      "available": true,
      "higgsfield_job_id": "higgsfield-job-id-xyz",
      "generation_prompt": "Brazilian woman, 30s, confident smile…",
      "approved_image": "/campaigns/C001/IMG/ML/A01R03/assets/character/approved/approved.png",
      "character_json": "/campaigns/C001/IMG/ML/A01R03/assets/character/character.json"
    }
  }
}
```

**Concept `status` values**

| Value | Meaning |
|---|---|
| `pending` | No prompt file and no image |
| `prompted` | `prompts/ad_{id}.md` written, image not yet generated |
| `generated` | Image found at `ads/ad-ml-{id}-{slug}.png` |

**`platform`** — inferred from `cwd.parent.name` (e.g. `IMG/ML/A01R03` → `"ML"`).

**`image` and `assets` paths** are absolute — pass to `GET /api/files/serve` to display in an `<img>` tag.

**`prompt_file`** — pass to `GET /api/files/read` to read the prompt markdown. `null` if not yet written.

**Errors** — `400` if `cwd` does not exist. Returns `concepts: []` if `ad_concepts.json` is missing or malformed.

---

## Health

### `GET /health`
```json
{ "status": "ok" }
```
