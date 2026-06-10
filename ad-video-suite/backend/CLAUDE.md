# CLAUDE.md — Backend

## Scope

**Hard boundary: only read or modify files inside `ad-video-suite/backend/`.**

- Do NOT read, open, or reference any file outside this directory — not `../frontend/`, not `../../`, nothing.
- Do NOT use Read, Edit, Write, Bash, or any tool on paths outside this directory.
- If a fix requires a change outside this directory, write one sentence describing what needs to change and stop. Do not make the edit, do not read the file to "understand context."
- This rule applies even when a task seems to require it. Backend scope is absolute.

## Development Commands

`claude_agent_sdk` requires Python 3.12 (installed in the `aiprog` conda env):

```bash
conda activate aiprog
cd backend && uvicorn main:app --port 8011 --reload
```

Or without activating:
```bash
cd backend && /home/fidel/.conda/envs/aiprog/bin/python3.12 -m uvicorn main:app --port 8011 --reload
```

First-time setup — set the campaigns root before creating anything:
```bash
curl -X PUT http://localhost:8011/api/settings \
  -H "Content-Type: application/json" \
  -d '{"base_path": "/absolute/path/to/your/campaigns"}'
```

## Architecture

FastAPI service that orchestrates a team of Claude SDK agents for producing direct-response video ads and ad images.

### Core Concept: The Folder Tree IS the Pipeline

There is no forced pipeline order. Agents are isolated — each one reads and writes directly in
whatever `cwd` the user selects. The campaign folder tree forms naturally as agents run:

```
{base_path}/
  C001/
    campaign.json
    agents/
      agents-config.yaml     ← per-campaign, generated at creation from template
      prompts/               ← per-campaign task instructions (one .md per agent)
    product/                 ← user drops product files here (read-only for agents)
    PRD/                     ← Product section
      images/                ← downloaded product assets
      product.json
      product_summary.md
      marketing_profile.json
      assets.json
    IMG/                     ← Image Ads section
      ML/                    ← Mercado Livre platform subfolder
        A01R01/              ← arc subfolder (cwd for ml-* agents, seeded by promote-arc)
          research.md
          A01.md
          A01R01.md
          hooks-index.md
          A01R01H01.md       ← one per hook
          assets/character/  ← copied from INT by promote-arc
            character.json
            approved/approved.png
          ad_plan.md
          ad_concepts.json
          ads/               ← generated ad images
    INT/                     ← Intelligence section
      research.md
      A01/                   ← created by Angles agent (cwd = INT/)
        A01.md
        A01R01/              ← created by Arcs agent (cwd = INT/A01/)
          A01R01.md
          timing-blueprint.json
          assets/character/  ← created by Character agent (cwd = INT/A01/A01R01/)
            character.json
            attempts/
            disapproved/
            approved/approved.png
          A01R01H01/         ← created by Hooks agent (cwd = INT/A01/A01R01/)
            A01R01H01.md
    SCE/                     ← Scenification section
      A01R01H01/             ← hook root (seeded by promote-hook)
        research.md
        A01.md
        A01R01.md
        timing-blueprint.json
        A01R01H01.md
        assets/character/    ← copied from INT by promote-hook
          character.json
          approved/approved.png
        script/
          script.json
        storyboard/
          M01.json           ← one file per moment
          M02.json
          storyboard.md      ← human-readable overview
          summary.md
        scene-specs/
          S01.json           ← one file per scene; declares storyboard_id upward reference
          S02.json
          summary.md
        shots/
          S01/               ← one subfolder per scene
            SH001.json       ← one file per shot; declares scene_id + needs_last_frame
          S02/
            SH002.json
          summary.md
        image-prompts/
          SH001.json         ← one file per shot (flat, no scene grouping)
          SH002.json
        image-generation/
          SH001/attempts|approved|disapproved/
        video-prompts/
          SH001/attempts|approved|disapproved/
          summary.md
        generated-clips/
          SH001/attempts|approved|disapproved/
        graphics/
```

### Naming Convention

| Level | Pattern | Example | Full path context |
|---|---|---|---|
| Campaign | `C###` | `C001` | root |
| Section | `[A-Z]{3}` | `INT`, `SCE`, `PRD`, `IMG` | `C001/INT` |
| Platform subfolder | `[A-Z]{2}` | `ML` | `C001/IMG/ML` |
| Angle | `A##` | `A01` | `C001/INT/A01` |
| Arc | `A##R##` | `A01R01` | `C001/INT/A01/A01R01` |
| Hook | `A##R##H##` | `A01R01H01` | `C001/INT/A01/A01R01/A01R01H01` |

Full reference (for Higgsfield, logs, exports): `C001-INT-A01R01H01`.

### Agent-to-Folder Matching: `cwd_pattern` + `sections`

Each agent declares two routing fields:

- **`cwd_pattern`** — regex run via `re.search()` against the **last segment** of the selected folder
- **`sections`** — list of 3-letter section codes where this agent is valid (empty = unrestricted)

Both must match for an agent to be offered. SCE agents additionally declare:

- **`required_inputs`** — list of `{path, produced_by}` dicts; paths are relative to `cwd` and support glob patterns (e.g. `image-generation/*/approved/*.json`)
- **`output_check`** — single path/glob relative to `cwd` that signals the agent has already run

These power the `agent_status(agent, cwd) → (status, missing)` helper in `agents/config.py`, which returns `"completed"` (output exists), `"ready"` (inputs present, no output yet), or `"blocked"` (required inputs missing). Inference extracts the section from the clicked path
(`_section_from_path()`) and passes it to `agents_for_folder()`.

**Anchoring matters**: `re.search` is used, not `re.fullmatch`. Use `^` and/or `$` anchors to
prevent accidental matches. Example: `[A-Z]{2}$` matches `IMG`, `INT`, `SCE`, etc. (all end in
two caps). `^[A-Z]{2}$` matches only exactly 2-letter strings like `ML`.

| Agent | `cwd_pattern` | `sections` | `add_dirs` | Folder type |
|---|---|---|---|---|
| product-creator | `[A-Z]{3}$` | `[PRD]` | — | PRD section folder |
| ml-planner | `A\d+R\d+$` | `[IMG]` | `['../../../PRD', '../../../INT']` | arc subfolder in IMG/ML/ |
| ml-creator | `A\d+R\d+$` | `[IMG]` | `['../../../PRD', '../../../INT']` | arc subfolder in IMG/ML/ |
| research, angles | `[A-Z]{3}$` | `[INT]` | — | INT section folder |
| arcs | `A\d+$` | `[INT]` | — | angle folder |
| timing, hooks | `A\d+R\d+$` | `[INT]` | — | arc folder |
| character | `A\d+R\d+$` | `[INT]` | `['..', '../..']` | arc folder |
| script, storyboard, scene-specs, shots, image-prompts, image-generation, video-prompts, generated-clips, graphics | `A\d+R\d+H\d+$` | `[SCE]` | — | hook root |

**Agent isolation** — each agent's permission scope is its `cwd` only. `add_dirs` is the sole
explicit exception: paths listed there are resolved to absolute paths in `ConversationSession.__init__()`
and passed as `--add-dir` CLI flags to `ClaudeAgentOptions`. Agents that declare no `add_dirs`
are strictly confined to their `cwd`.

**Higgsfield agents require `mcp_overrides`** — listing Higgsfield tools in `allowed_tools` is
necessary but not sufficient. The agent must also have an entry in the top-level `mcp_overrides`
section of `agents-config.yaml` with `strict_mcp_config: true`. Agents wired to Higgsfield:
`ml-creator`, `character`, `image-generation`, `generated-clips`.

**Adding a new agent**: see `agents/HOW-TO-ADD-AGENTS.md` for a step-by-step guide.

### Character Sharing Across Sections

The `character` agent runs in `INT/A##R##/` and produces a single approved reference image
for the main character of that arc. The character is then propagated to both downstream sections
automatically at promotion time:

- **`promote-hook`** → copies `INT/A##/A##R##/assets/character/` into `SCE/A##R##H##/assets/character/`
  — all hooks of the arc get the same character
- **`promote-arc`** → copies `INT/A##/A##R##/assets/character/` into `IMG/ML/A##R##/assets/character/`
  — ad images for that arc use the same character

The `character.json` file written by the character agent includes a `higgsfield_job_id` field.
Downstream agents pass this directly as `medias[].value` in Higgsfield API calls — no re-upload
needed. Consuming agents:

| Agent | How character is used |
|---|---|
| `scene-specs` | Reads `visual_identity` to write consistent subject/visual_description fields |
| `image-prompts` | Embeds `generation_prompt` verbatim in first/last frame prompts |
| `image-generation` | Passes `higgsfield_job_id` as reference media to `generate_image` |
| `generated-clips` | Passes `higgsfield_job_id` as reference media to `generate_video` |
| `ml-creator` | Passes `higgsfield_job_id` as reference media for human-model ad concepts |

All character references are optional — agents check for `assets/character/character.json`
and proceed without it if absent.

### All Agents Are WebSocket (persistent multi-turn)

The WS endpoint (`/ws/agents/{name}/chat?cwd={path}&campaign={slug}`) always fires `basic_prompt`
on connect. The agent reads its `cwd`, executes its task, then stays alive for follow-up refinements.

**WS pre-check (SCE agents)** — before opening the session the handler calls `agent_status()` and
rejects the connection with an `{"type":"error"}` message if status is `"blocked"`. This is a
safety net; the UI should already know the status from `GET /api/tree` or `POST /api/launch`.

**SCE agent prompt structure** — every SCE agent prompt is structured in this order:
1. **Inputs guard** — agent checks required files itself and tells the user "I shouldn't be running — missing: [files]" if anything is absent. Acts as a second safety net while the backend status system is being validated.
2. **Resume check** — if outputs already exist, inventories them, displays `summary.md` if present, suggests the next action, and waits for instruction. Never overwrites automatically. For per-item agents (storyboard, scene-specs, shots, image-prompts) the user can request a **selective edit** — the agent rewrites only the specific item file and leaves the rest untouched.
3. **Task execution** — runs only if guards pass.
4. **Summary output** — storyboard, scene-specs, shots, and video-prompts each write a `summary.md` alongside their output: a few prose sentences describing what was produced, in the agent's own voice.

**SCE artifact structure — vertical channels** — each pipeline level uses per-item files so surgical re-runs are structural rather than requiring any tracking mechanism:

| Level | Files | Upward reference |
|---|---|---|
| Storyboard | `storyboard/M{##}.json` | — (root level) |
| Scene-specs | `scene-specs/S{##}.json` | `storyboard_id` → parent moment |
| Shots | `shots/{scene_id}/SH{###}.json` | `scene_id` → parent scene |
| Image-prompts | `image-prompts/SH{###}.json` | `shot_id` → parent shot |
| Image-generation | `image-generation/{shot_id}/attempts\|approved\|disapproved/` | — |
| Video-prompts | `video-prompts/{shot_id}/attempts\|approved\|disapproved/` | — |
| Generated-clips | `generated-clips/{shot_id}/attempts\|approved\|disapproved/` | — |

**`needs_last_frame`** — boolean field on every shot JSON. `false` for terminal shots (`continuity_to: null`) and very short static shots; `true` otherwise. Controls whether a last-frame keyframe is generated and passed as `end_image` to Higgsfield. Set by the shots agent; consumed by image-prompts, image-generation, video-prompts, and generated-clips.

**`camera_motion` / `subject_motion` in video-prompts** — scaffolding fields written for human review legibility only. Neither field is passed to Higgsfield. The `motion_prompt` field is the authoritative string submitted to the video model.

### Campaign Management

- `POST /api/campaigns {"name": "..."}` — auto-generates `C001`, `C002`… slug, scaffolds folder, returns `path`
- `backend/settings.json` stores only `base_path` — no active campaign concept
- `PUT /api/settings {"base_path": "..."}` — set before creating any campaigns

Scaffolded sections at campaign creation (hardcoded in `core/campaigns.py`):
`PRD/`, `PRD/images/`, `IMG/`, `IMG/ML/`, `INT/`, `SCE/`

**Propagating template changes to existing campaigns** — after editing `agents-config.template.yaml`
or any file in `agents/prompts/`, run:
```python
# from backend/
from agents.config import resolve_campaign_config, get_settings
base = get_settings()["base_path"]
for slug in ["C001", "C002", "C003"]:
    content = resolve_campaign_config(slug, base)
    open(f"{base}/{slug}/agents/agents-config.yaml", "w").write(content)
```
Then copy updated prompts:
```bash
for c in C001 C002 C003; do
  cp agents/prompts/*.md {base_path}/$c/agents/prompts/
done
```

### API Reference

Full endpoint documentation lives in `API.md` — that file is the single source of truth for request/response shapes, status codes, and field semantics. Do not duplicate API details here.

### Key Files

- `agents/agents-config.template.yaml` — source of truth for agent definitions; versioned with the app
- `agents/HOW-TO-ADD-AGENTS.md` — step-by-step guide for adding new agents or sections
- `agents/config.py` — `AgentConfig` dataclass (`required_inputs`, `output_check` fields), `agent_status()`, `load_config()`, `resolve_campaign_config()`, `agents_for_folder()`
- `agents/conversation_agent.py` — `ConversationSession` wraps `ClaudeSDKClient`; resolves `add_dirs` and passes `--add-dir` flags
- `agents/prompts/` — app-level stub prompts copied into each new campaign's `agents/prompts/`
- `core/campaigns.py` — campaign CRUD, auto slug generation, folder scaffold (hardcoded section list)
- `core/promotions.py` — `promote_hook()` and `promote_arc()`: copy INT files and `assets/character/` into SCE and IMG respectively
- `routers/agents.py` — REST + WS handlers, tree builder, infer-agent, promote-hook, promote-arc endpoints
