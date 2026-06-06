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
      ML/                    ← Mercado Livre platform subfolder (cwd for ml-* agents)
        ad_plan.md
        ad_concepts.json
        ads/                 ← generated ad images
    INT/                     ← Intelligence section
      research.md
      A01/                   ← created by Angles agent (cwd = INT/)
        A01.md
        A01R01/              ← created by Arcs agent (cwd = INT/A01/)
          A01R01.md
          timing-blueprint.json
          A01R01H01/         ← created by Hooks agent (cwd = INT/A01R01/)
            A01R01H01.md
    SCE/                     ← Scenification section
      A01R01H01/             ← hook root
        script/
        scene-specs/
        shots/
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

Both must match for an agent to be offered. Inference extracts the section from the clicked path
(`_section_from_path()`) and passes it to `agents_for_folder()`.

**Anchoring matters**: `re.search` is used, not `re.fullmatch`. Use `^` and/or `$` anchors to
prevent accidental matches. Example: `[A-Z]{2}$` matches `IMG`, `INT`, `SCE`, etc. (all end in
two caps). `^[A-Z]{2}$` matches only exactly 2-letter strings like `ML`.

| Agent | `cwd_pattern` | `sections` | `add_dirs` | Folder type |
|---|---|---|---|---|
| product-creator | `[A-Z]{3}$` | `[PRD]` | — | PRD section folder |
| ml-planner | `^[A-Z]{2}$` | `[IMG]` | `['../../PRD', '../../INT']` | platform subfolder |
| ml-creator | `^[A-Z]{2}$` | `[IMG]` | `['../../PRD', '../../INT']` | platform subfolder |
| research, angles | `[A-Z]{3}$` | `[INT]` | — | INT section folder |
| arcs | `A\d+$` | `[INT]` | — | angle folder |
| timing, hooks | `A\d+R\d+$` | `[INT]` | — | arc folder |
| script | `A\d+R\d+H\d+$` | `[SCE]` | — | hook root |
| storyboard, scene-specs, shots, image-prompts, image-generation, video-prompts, generated-clips, graphics | `A\d+R\d+H\d+$` | `[SCE]` | — | hook root |

**Agent isolation** — each agent's permission scope is its `cwd` only. `add_dirs` is the sole
explicit exception: paths listed there are resolved to absolute paths in `ConversationSession.__init__()`
and passed as `--add-dir` CLI flags to `ClaudeAgentOptions`. Agents that declare no `add_dirs`
are strictly confined to their `cwd`.

**Higgsfield agents require `mcp_overrides`** — listing Higgsfield tools in `allowed_tools` is
necessary but not sufficient. The agent must also have an entry in the top-level `mcp_overrides`
section of `agents-config.yaml` with `strict_mcp_config: true`. See `ml-creator` and
`image-generation` for the pattern.

**Adding a new agent**: see `agents/HOW-TO-ADD-AGENTS.md` for a step-by-step guide.

### All Agents Are WebSocket (persistent multi-turn)

The WS endpoint (`/ws/agents/{name}/chat?cwd={path}&campaign={slug}`) always fires `basic_prompt`
on connect. The agent reads its `cwd`, executes its task, then stays alive for follow-up refinements.
No fresh/resume detection — if the agent finds existing outputs in its cwd, it adapts naturally.

### Campaign Management

- `POST /api/campaigns {"name": "..."}` — auto-generates `C001`, `C002`… slug, scaffolds folder, returns `path`
- `backend/settings.json` stores only `base_path` — no active campaign concept
- `PUT /api/settings {"base_path": "..."}` — set before creating any campaigns

Scaffolded sections at campaign creation (hardcoded in `core/campaigns.py`):
`PRD/`, `PRD/images/`, `IMG/`, `IMG/ML/`, `INT/`, `SCE/`

### Launching an Agent: `POST /api/launch`

The primary endpoint for the UI. Takes the folder path the user clicked and returns everything
needed to open a WS connection — including agent inference and disambiguation.

```
POST /api/launch {"path": "/campaigns/C001/INT/A02"}
```

**Unambiguous** (one agent matches):
```json
{ "ambiguous": false, "agent_id": "arcs", "agent_name": "Arc Generator",
  "campaign": "C001", "cwd": "/campaigns/C001/INT/A02",
  "ws_url": "/ws/agents/arcs/chat?cwd=...&campaign=C001" }
```

**Ambiguous** (multiple agents match):
```json
{ "ambiguous": true, "campaign": "C001", "cwd": "...",
  "candidates": [{"id": "timing", ...}, {"id": "hooks", ...}] }
```
UI shows a picker → re-calls with `agent_id` set.

**Errors (400):** path not found · no agent matches · `agent_id` doesn't fit the folder.

### Key API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/launch` | Infer agent from path, return WS URL |
| `GET` | `/api/tree` | Full campaign tree with `available_agents` per node |
| `GET` | `/api/infer-agent?path=...&campaign=...` | Agents that match a folder (lightweight) |
| `GET` | `/api/agents?campaign=...` | Agent list (with `cwd_pattern`) |
| `POST` | `/api/promote-hook` | Seed INT files into SCE/{hook_id}/ (idempotent) |
| `POST` | `/api/campaigns` | Create new campaign (auto C### slug) |
| `GET` | `/api/campaigns` | List all campaigns |
| `GET` | `/api/campaigns/{slug}` | Campaign metadata + path |
| `WS` | `/ws/agents/{name}/chat?cwd=...&campaign=...` | Agent session |
| `GET` | `/api/files/list?path=...` | Browse filesystem |
| `GET` | `/api/files/read?path=...` | Read a file |
| `POST` | `/api/files/write` | Write a file |

### Key Files

- `agents/agents-config.template.yaml` — source of truth for agent definitions; versioned with the app
- `agents/HOW-TO-ADD-AGENTS.md` — step-by-step guide for adding new agents or sections
- `agents/config.py` — `AgentConfig` dataclass, `load_config()`, `resolve_campaign_config()`, `agents_for_folder()`
- `agents/conversation_agent.py` — `ConversationSession` wraps `ClaudeSDKClient`; resolves `add_dirs` and passes `--add-dir` flags
- `agents/prompts/` — app-level stub prompts copied into each new campaign's `agents/prompts/`
- `core/campaigns.py` — campaign CRUD, auto slug generation, folder scaffold (hardcoded section list)
- `core/promotions.py` — `promote_hook()`: copies INT files into a flat `SCE/{hook_id}/` folder
- `routers/agents.py` — REST + WS handlers, tree builder, infer-agent, promote-hook endpoints
