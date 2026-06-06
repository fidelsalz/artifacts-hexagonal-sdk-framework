# Ad Video Suite

A backend service that runs a team of Claude AI agents to produce 35-second direct-response video ads. Each agent is an expert in one creative step — research, angles, arcs, hooks, scripting, scene specs, shot lists, and graphics planning.

There is no forced pipeline. Agents are isolated and work in whatever folder you point them at. The campaign folder tree builds naturally as you work.

---

## How It Works

### The Folder Tree Is the Pipeline

When you launch an agent you choose a folder — that folder is the agent's entire workspace. It reads what's there and writes its output back into it. No hidden state, no message-passing between agents.

```
campaigns/
  C001/                         ← campaign
    product/                    ← you drop product files here
    research.md                 ← Research agent output
    C001A01/                    ← Angles agent creates this
      C001A01.md
      C001A01R02/               ← Arcs agent creates this (inside angle folder)
        C001A01R02.md
        timing-blueprint.json
        C001A01R02H03/          ← Hooks agent creates this (inside arc folder)
          C001A01R02H03.md
          script.json
          scene-specs.json
          shot-list.json
          graphics-plan.json
    C001A02/
      ...
```

### Naming Convention

Every folder name encodes its full lineage:

| Segment | Meaning | Example |
|---|---|---|
| `C###` | Campaign | `C001` |
| `C###A##` | Angle # of campaign | `C001A02` |
| `C###A##R##` | Arc # of that angle | `C001A02R01` |
| `C###A##R##H##` | Hook # of that arc | `C001A02R01H03` |

This means you can work non-linearly. Run Angles twice on the same campaign. Explore three different arcs under the same angle. Every branch is independent.

### Agents and Where They Work

| Agent | Works in | Creates |
|---|---|---|
| **Research** | `C###/` (campaign root) | `research.md` |
| **Angles** | `C###/` (campaign root) | `C###A01/`, `C###A02/`… |
| **Arcs** | `C###A##/` (angle folder) | `C###A##R01/`, `C###A##R02/`… |
| **Timing** | `C###A##R##/` (arc folder) | `timing-blueprint.json` |
| **Hooks** | `C###A##R##/` (arc folder) | `C###A##R##H01/`… |
| **Script** | `C###A##R##H##/` (hook folder) | `script.json`, `script-readthrough.md` |
| **Scene Specs** | `C###A##R##H##/` (hook folder) | `scene-specs.json` |
| **Shot List** | `C###A##R##H##/` (hook folder) | `shot-list.json` |
| **Graphics** | `C###A##R##H##/` (hook folder) | `graphics-plan.json` |

---

## Setup

### Requirements

- Python 3.12 with `claude_agent_sdk` installed (conda env `aiprog`)
- An Anthropic API key available in the environment

### Run the backend

```bash
conda activate aiprog
cd backend
uvicorn main:app --port 8011 --reload
```

### Point it at your campaigns folder

```bash
curl -X PUT http://localhost:8011/api/settings \
  -H "Content-Type: application/json" \
  -d '{"base_path": "/path/to/your/campaigns"}'
```

---

## Usage

### 1. Create a campaign

```bash
curl -X POST http://localhost:8011/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "Running Shoes Q4"}'
# → { "slug": "C001", "name": "Running Shoes Q4", ... }
```

This creates `C001/` with a `product/` folder and a pre-configured `agents/` directory.

### 2. Drop your product files

Put any of these into `C001/product/`:

| File | Contents |
|---|---|
| `info.md` | Product name, category, price, key claims |
| `specs.md` | Technical specs and features |
| `reviews.md` | Real customer reviews (copy/paste from Mercado Livre) |
| `competitors.md` | Competitor products and their positioning |

### 3. Browse the campaign tree

```bash
curl http://localhost:8011/api/tree
```

Returns every campaign and all its subfolders. Each node includes `available_agents` — the agents that can work in that folder.

### 4. Launch an agent

`POST /api/launch` is the main UI endpoint. Send the path of whatever folder the user clicked:

```bash
curl -X POST http://localhost:8011/api/launch \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/campaigns/C001"}'
```

**When one agent matches** the response is ready to use:
```json
{
  "ambiguous": false,
  "agent_id": "research",
  "agent_name": "Research Agent",
  "campaign": "C001",
  "cwd": "/path/to/campaigns/C001",
  "ws_url": "/ws/agents/research/chat?cwd=/path/to/campaigns/C001&campaign=C001"
}
```

**When multiple agents match** (e.g. clicking an arc folder returns both `timing` and `hooks`):
```json
{
  "ambiguous": true,
  "campaign": "C001",
  "cwd": "/path/to/campaigns/C001/C001A02/C001A02R01",
  "candidates": [
    { "id": "timing", "name": "Timing Blueprint", "role": "..." },
    { "id": "hooks",  "name": "Hook Generator",   "role": "..." }
  ]
}
```
Show the user a picker, then re-call with `agent_id`:
```bash
curl -X POST http://localhost:8011/api/launch \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/campaigns/C001/C001A02/C001A02R01", "agent_id": "hooks"}'
```

### 5. Connect the WebSocket

Use the `ws_url` from the launch response. The agent immediately reads its folder, runs its full task, and stays connected for follow-up messages.

**WebSocket message protocol:**

```jsonc
// Client → server
{ "type": "message",    "text": "give me 2 more angle options" }
{ "type": "interrupt" }       // stop current generation
{ "type": "new_session" }     // restart from scratch

// Server → client
{ "type": "connected",    "agent": "angles", "cwd": "..." }
{ "type": "assistant",    "text": "..." }       // streamed text
{ "type": "result",       "total_cost_usd": 0.003, ... }
{ "type": "turn_complete" }
{ "type": "error",        "message": "..." }
```

---

## Agent Prompts

Each campaign gets its own copy of the agent prompts at `C###/agents/prompts/`. Edit them to tune an agent's behaviour for a specific product category without affecting other campaigns.

The app-level stubs live at `backend/agents/prompts/` and are copied into every new campaign.

---

## Adding a New Agent

1. Add an entry to `backend/agents/agents-config.template.yaml`:

```yaml
adimage:
  id:              "adimage"
  name:            "Ad Image Generator"
  role:            "Reads product info, generates image concepts and Higgsfield prompts"
  comm_type:       ws
  cwd_pattern:     'C\d{3}$'          # campaign root
  prompt_file:     "{campaign_dir}/agents/prompts/adimage.md"
  basic_prompt:    *basic_prompt
  model:           *model
  permission_mode: *dontask_mode
  allowed_tools:   *write_tools
```

2. Create `backend/agents/prompts/adimage.md` with the task instructions.

3. New campaigns pick it up automatically. Existing campaigns: copy the entry into `C###/agents/agents-config.yaml` and add the prompt file.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/settings` | Get `base_path` |
| `PUT` | `/api/settings` | Set `base_path` |
| `GET` | `/api/campaigns` | List all campaigns |
| `POST` | `/api/campaigns` | Create campaign — auto `C###` slug, returns `path` |
| `GET` | `/api/campaigns/{slug}` | Campaign metadata + `path` |
| `GET` | `/api/tree` | Full tree with `available_agents` per node |
| `POST` | `/api/launch` | Infer agent from clicked path, return WS URL |
| `GET` | `/api/infer-agent?path=&campaign=` | Lightweight: agents that match a folder |
| `GET` | `/api/agents?campaign=` | Agent definitions with `cwd_pattern` |
| `GET` | `/api/agents/{name}/config?campaign=` | Single agent config |
| `WS` | `/ws/agents/{name}/chat?cwd=&campaign=` | Agent session |
| `GET` | `/api/files/list?path=` | List directory contents |
| `GET` | `/api/files/read?path=` | Read a file |
| `POST` | `/api/files/write` | Write a file (`{path, content}`) |
| `GET` | `/health` | Health check |
