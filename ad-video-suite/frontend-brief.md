# Frontend Brief — Ad Video Suite

## What to build

A UI for a backend that runs Claude AI agents to produce 35-second direct-response video ads.
The backend is FastAPI on `http://localhost:8011`, already fully built. Build the frontend at
`ad-video-suite/frontend/`.

---

## Tech stack

- **SvelteKit** + **Svelte 5 runes** (`$state`, `$derived`, `$effect`) — not the legacy Options API
- **Tailwind CSS v4**, zinc color scale, light theme
- **shadcn-svelte** (bits-ui) for UI components
- API base URL: `http://localhost:8011` (configurable via `VITE_API_BASE_URL`)

---

## Layout — three panels

```
┌─────────────────┬──────────────────────────────┬─────────────────┐
│  Campaign Tree  │        Agent Chat            │  File Browser   │
│                 │                              │                 │
│  C001           │  [Research Agent — C001]     │  C001/          │
│  ├ C001A01      │                              │  ├ product/     │
│  │ └ C001A01R01 │  > Reading product info...   │  ├ research.md  │
│  └ C001A02      │  > Found 3 key pain points   │  └ C001A01/     │
│                 │  > Writing research.md...    │                 │
│  C002           │                              │                 │
│  └ ...          │  [text input + send]         │                 │
└─────────────────┴──────────────────────────────┴─────────────────┘
```

---

## Core interaction: clicking a tree node launches an agent

### Step 1 — user clicks a node

```
POST /api/launch
{ "path": "/absolute/path/to/clicked/folder" }
```

**Unambiguous response** (one agent matches the folder) — open WS immediately:
```json
{
  "ambiguous": false,
  "agent_id":   "arcs",
  "agent_name": "Arc Generator",
  "role":       "Generates emotional arc variants for the chosen angle",
  "campaign":   "C001",
  "cwd":        "/path/to/C001/C001A02",
  "ws_url":     "/ws/agents/arcs/chat?cwd=/path/to/C001/C001A02&campaign=C001"
}
```

**Ambiguous response** (multiple agents share the folder pattern) — show a picker:
```json
{
  "ambiguous":  true,
  "campaign":   "C001",
  "cwd":        "/path/to/C001/C001A02/C001A02R01",
  "candidates": [
    { "id": "timing", "name": "Timing Blueprint", "role": "..." },
    { "id": "hooks",  "name": "Hook Generator",   "role": "..." }
  ]
}
```

### Step 2 — if ambiguous, user picks an agent, re-call with agent_id

```
POST /api/launch
{ "path": "/path/to/C001/C001A02/C001A02R01", "agent_id": "hooks" }
```
→ returns the unambiguous success shape above.

### Step 3 — connect WebSocket

```
ws://localhost:8011{ws_url}
```

---

## WebSocket protocol

**Server → client events:**

```jsonc
{ "type": "connected",    "agent": "hooks", "cwd": "/..." }
{ "type": "assistant",    "text": "..." }      // streamed; append to chat display
{ "type": "result",       "total_cost_usd": 0.003, "duration_ms": 8200,
                          "input_tokens": 1200, "output_tokens": 540 }
{ "type": "turn_complete" }                    // agent finished this turn
{ "type": "error",        "message": "..." }
{ "type": "interrupted" }                      // after client sends interrupt
{ "type": "session_reset" }                    // after client sends new_session
```

**Client → server messages:**

```jsonc
{ "type": "message",    "text": "give me 2 more hook variants" }
{ "type": "interrupt" }                        // stop current generation
{ "type": "new_session" }                      // wipe cwd outputs and restart
```

---

## Campaign management

### First-time setup

On load, check `GET /api/settings`. If `base_path` is empty, show a setup screen:

```
PUT /api/settings
{ "base_path": "/absolute/path/to/campaigns/folder" }
```

### Create a campaign

```
POST /api/campaigns
{ "name": "Running Shoes Q4" }

→ { "slug": "C001", "name": "Running Shoes Q4",
    "created_at": "...", "path": "/campaigns/C001" }
```

Slug is auto-generated (`C001`, `C002`…). After creation, refresh the tree.

### List campaigns

```
GET /api/campaigns
→ [{ "slug": "C001", "name": "...", "created_at": "..." }, ...]
```

---

## Campaign tree

```
GET /api/tree
```

Returns an array of campaign nodes. Each node:

```json
{
  "name":             "C001",
  "path":             "/absolute/path/to/campaigns/C001",
  "available_agents": ["research", "angles"],
  "children": [
    {
      "name":             "C001A01",
      "path":             "/absolute/.../C001/C001A01",
      "available_agents": ["arcs"],
      "children": [
        {
          "name":             "C001A01R02",
          "path":             "/absolute/.../C001A01/C001A01R02",
          "available_agents": ["timing", "hooks"],
          "children":         []
        }
      ]
    }
  ]
}
```

Only folders that match the naming convention appear in the tree. The tree grows as agents run
and create new subfolders — refresh after each agent completes.

**Naming convention:**
- `C###` — campaign root
- `C###A##` — angle (created by Angles agent)
- `C###A##R##` — arc (created by Arcs agent)
- `C###A##R##H##` — hook (created by Hooks agent)

---

## File browser

```
GET /api/files/list?path=/absolute/path/to/folder
→ { "path": "...", "entries": [
    { "name": "research.md", "type": "file", "path": "/..." },
    { "name": "C001A01",     "type": "dir",  "path": "/..." }
  ]}

GET /api/files/read?path=/absolute/path/to/file
→ { "path": "...", "content": "..." }

POST /api/files/write
{ "path": "/absolute/path/to/file", "content": "..." }
→ { "ok": true }
```

---

## Multiple simultaneous agents

There is no "active campaign" — users can have multiple agent panels open at once (one WS each),
working on different campaigns or different branches of the same campaign. Design accordingly:
tabs or a panel list that keeps each WS alive while switching views.

---

## All endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/settings` | Get `base_path` |
| `PUT` | `/api/settings` | Set `base_path` |
| `GET` | `/api/campaigns` | List all campaigns |
| `POST` | `/api/campaigns` | Create campaign |
| `GET` | `/api/campaigns/{slug}` | Campaign detail + `path` |
| `GET` | `/api/tree` | Full campaign tree |
| `POST` | `/api/launch` | Infer agent, return WS URL |
| `GET` | `/api/infer-agent?path=&campaign=` | Lightweight folder→agents lookup |
| `GET` | `/api/agents?campaign=` | Agent list with `cwd_pattern` |
| `WS` | `/ws/agents/{name}/chat?cwd=&campaign=` | Agent session |
| `GET` | `/api/files/list?path=` | List directory |
| `GET` | `/api/files/read?path=` | Read file |
| `POST` | `/api/files/write` | Write file |
| `GET` | `/health` | Health check |
