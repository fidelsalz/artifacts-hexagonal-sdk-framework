# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Scope restriction

Only read or modify files inside this directory (`ad-video-suite/frontend/`).
Do not touch files in `../backend/` or anywhere else outside this cwd.
If a fix requires changes outside this directory, describe what needs to change
and stop — do not make the edit.

## Development Commands

```bash
npm run dev          # SvelteKit dev server on port 5173
npm run build        # production build
npm run check        # svelte-check type checking
npm run lint         # prettier + eslint
npm run format       # prettier auto-fix
```

Backend runs on port 8011 — see `../CLAUDE.md` for backend start commands.

## Architecture

This is the frontend for **Ad Video Suite**, a UI that drives a team of Claude SDK agents to produce 35-second direct-response video ads. It is a SvelteKit app that talks exclusively to the FastAPI backend at `http://localhost:8011` (configured in `src/lib/config.ts`, overridable via `VITE_API_BASE_URL`).

### Core Concept: Folder Tree = Pipeline

There is no explicit pipeline order. The campaign folder tree grows as agents run. The UI exposes this tree and lets users launch agents by clicking a folder node. The backend infers which agent(s) match based on the folder name pattern — the frontend is a thin view over that API.

### Routes

| Route | Purpose |
|---|---|
| `/` | Campaign list + first-time base-path setup. Campaign links open in `target="_blank"`. |
| `/new-campaign` | Create a campaign (auto-generates `C001`, `C002`… slug) |
| `/campaigns/[slug]` | Full campaign workspace — opens in a new tab, no back navigation |
| `/dashboard` | Stats overview: stat cards + live sessions table |
| `/settings` | Backend settings (`base_path`, `max_active_campaigns`) |
| `/test` | API health check panel (dev only) |

### Tech Stack

- Svelte 5 runes (`$state`, `$props`, `$derived`, `$effect`) — no legacy Options API
- `SvelteSet` / `SvelteMap` from `svelte/reactivity` for reactive collections (plain `Set`/`Map` mutations are **not** tracked by Svelte 5)
- Tailwind CSS v4 (single `@import 'tailwindcss'` in `layout.css`)
- `bits-ui` for nav components (`NavigationMenu`, `Separator`, `Label`)
- `marked` for Markdown rendering in `FileViewer`
- Styling: slate color scale, white/slate-50 backgrounds, emerald accent for primary actions

### Shared UI Components (`src/lib/components/ui/`)

- `button.svelte` — variants: `default`, `outline`, `ghost`, `destructive`; sizes: `default`, `sm`
- `input.svelte` — bindable `value`, forwards all `HTMLInputAttributes`
- `label.svelte` — wraps `Label.Root` from bits-ui

### App Navigation (`AppNav.svelte`)

Shared header used by `/`, `/dashboard`, and `/settings`. Accepts an optional `right` snippet for page-specific actions (e.g. "+ New Campaign" on the home page).

---

## Campaign Workspace (`/campaigns/[slug]`)

The campaign page is a fixed-height (`h-screen`) workspace. It opens in its own tab — "Close campaign" stops all agents and closes the tab via `window.close()`.

### Layout

```
┌──── header: ◀/▶ tree toggle · campaign name/slug · session count · Close campaign ──┐
│                                                                                      │
│  [LEFT sidebar, draggable]       [RIGHT scrollable main]                            │
│  CampaignTree                    ▾ File      (collapsible)                          │
│  (always mounted, CSS width)     ▾ Agents    (collapsible)                          │
│                                  ▾ Agent chat (collapsible)                         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

**Left sidebar:**
- CSS width transition between `sidebarWidth`px and `0` — never unmounted, tree state preserved
- Draggable right edge (`mousedown` on handle → `mousemove`/`mouseup` on `document`), clamped 160–520px
- Toggle button (`◀`/`▶`) in the header bar
- `resizing` state removes `transition-[width]` during drag for instant feedback

**Right main:**
- Plain `overflow-y-auto` block (not flex-col) — sections stack and scroll naturally
- Each section has a clickable header row with `▾`/`▸` chevron to collapse/expand
- `fileSection` and `chatSection` refs used for `scrollIntoView` on file click / session launch

### Shared Types (`src/lib/types.ts`)

`TreeNodeData`, `AgentCandidate`, `FileEntry`, `CampaignData`, `ChatMsg`, `SessionStatus`, `SessionEntry`.

### Session Store (`src/lib/stores/sessionStore.svelte.ts`)

Module-level `$state` — survives component remounts and tab switches within the page.

```ts
export const sessionStore = $state({
  sessions: SessionEntry[],   // keyed by `${agentId}::${cwd}`
  activeKey: string | null,
});
```

**Key functions:** `launchSession`, `setActiveSession`, `getSession`, `getSessionsForCwd`, `pushMessage`, `setStatus`, `setSessionInfo`, `incrementTurnCount`, `setError`, `closeAllSessions`.

**Critical mutation rule:** Always mutate session properties directly (`sessions[i].status = x`), never spread-replace (`sessions[i] = {...}`) — replacement changes the object reference and disrupts the keyed `{#each}` that keeps WS panels mounted.

### Session Persistence Pattern

Sessions are keyed by `${agentId}::${cwd}`. Always-mounted, CSS-hidden when inactive:

```svelte
{#each sessionStore.sessions as session (session.key)}
  <div class={session.key === sessionStore.activeKey ? '' : 'hidden'}>
    <AgentChatPanel sessionKey={session.key} />
  </div>
{/each}
```

`(session.key)` on `{#each}` ensures Svelte never destroys existing panels on array append — keeps WebSocket connections alive across folder navigation.

### Components

**`CampaignTree.svelte`**
- Props: `{ treeNode, onFolderSelect, onFileSelect, onRefresh? }`
- `onFileSelect`: `(path: string, parentNode: TreeNodeData) => void` — carries parent so agents panel syncs to the right folder level on file click
- Uses `SvelteSet`/`SvelteMap` for `expandedPaths`, `fileEntries`, `loadingPaths`
- Flat derived list via `$derived(buildFlatList(treeNode, 0))`
- `onRefresh`: busts `fileEntries` cache for all expanded paths, re-fetches them, then calls parent's tree refresh
- Drag handle at bottom-right: `↺ refresh` button

**`FileViewer.svelte`**
- Props: `{ filePath: string | null }`
- `$effect` re-fetches on path change
- `.md` files: rendered via `marked.parse()` with scoped prose styles; **Source / Preview** toggle button
- Other files: plain `<pre>` block
- Edit mode: `<textarea>` + `Ctrl+S` save / `Esc` cancel → `POST /api/files/write`

**`AgentLauncher.svelte`**
- Props: `{ selectedPath, selectedAgents, campaign, onSessionLaunched }`
- `existingSessions = $derived(getSessionsForCwd(selectedPath))` — reactive
- Launch: `POST /api/launch` → inline disambiguation picker on `ambiguous: true`
- Error banner is dismissible (✕ button clears `launchError`)
- Resume: `setActiveSession(key)` + `onSessionLaunched(key)`

**`AgentChatPanel.svelte`**
- Props: `{ sessionKey: string }`
- Fixed height `h-[520px]`; messages div is `flex-1 overflow-y-auto`
- WS URL: `API_BASE.replace(/^http/, 'ws') + session.wsUrl`
- Ephemeral local state: `ws`, `connected`, `thinking`, `inputText` — panels never remounted so this is fine
- **Never wrap with `{#key sessionKey}`** — destroys the WS subprocess

---

## Dashboard (`/dashboard`)

Fetches `/api/campaigns` and `/api/sessions` in parallel on mount and on manual Refresh.

**Stat cards (4):** Campaigns · Variations · Live sessions · Active campaigns

**Live sessions table:** Campaign · Agent · Folder (last 2 path segments) · Running for (elapsed from `started_at`)

`variations_generated` on each campaign = count of `C###A##R##H##` hook-level folders (computed live by backend on each request via `rglob`).

---

## Backend API Reference (`http://localhost:8011`)

### Settings

| Method | Path | Body / Params | Response |
|---|---|---|---|
| `GET` | `/api/settings` | — | `{ base_path, max_active_campaigns }` |
| `PUT` | `/api/settings` | `{ base_path?, max_active_campaigns? }` | updated settings |

### Campaigns

| Method | Path | Body / Params | Response |
|---|---|---|---|
| `GET` | `/api/campaigns` | — | array of campaign objects |
| `POST` | `/api/campaigns` | `{ name? }` | `{ slug, name, path, created_at, variations_generated }` |
| `GET` | `/api/campaigns/{slug}` | — | campaign metadata or 404 |

### Agents & Tree

| Method | Path | Body / Params | Response |
|---|---|---|---|
| `GET` | `/api/agents` | `?campaign=C001` | `[{ id, name, role, comm_type, cwd_pattern }]` |
| `GET` | `/api/agents/{name}/config` | `?campaign=C001` | full config incl. `model` |
| `GET` | `/api/tree` | — | full campaign tree with `available_agents` per node |
| `GET` | `/api/infer-agent` | `?path=...&campaign=...` | `[{ id, name, role }]` |
| `POST` | `/api/launch` | `{ path, agent_id? }` | see below |
| `GET` | `/api/sessions` | — | `{ active_campaigns, sessions }` |

**`POST /api/launch` responses:**

```json
// Unambiguous
{ "ambiguous": false, "agent_id": "hooks", "agent_name": "Hook Writer",
  "role": "...", "campaign": "C001", "cwd": "/path/C001A01R01",
  "ws_url": "/ws/agents/hooks/chat?cwd=...&campaign=C001" }

// Ambiguous — show picker, re-call with agent_id
{ "ambiguous": true, "campaign": "C001", "cwd": "/path/C001A01R01",
  "candidates": [{ "id": "timing", "name": "...", "role": "..." }, ...] }
```

Errors return HTTP 400: path not found · no agent matches · `agent_id` doesn't fit this folder.

### Files

| Method | Path | Body / Params | Response |
|---|---|---|---|
| `GET` | `/api/files/list` | `?path=...` | `{ path, entries: [{ name, type, path }] }` |
| `GET` | `/api/files/read` | `?path=...` | `{ path, content }` — text only, not for binary files |
| `POST` | `/api/files/write` | `{ path, content }` | `{ ok: true }` |

> **Media files:** `/api/files/read` returns JSON text — unsuitable for binary. A future `GET /api/files/serve?path=...` endpoint (streams raw bytes with correct Content-Type) is needed to support inline video/audio/image playback in `FileViewer`.

### Health

`GET /health` → `{ status: "ok" }`

### Concurrency limits

- Max 3 active campaigns simultaneously (configurable via `PUT /api/settings { max_active_campaigns }`).
- Exceeding limit: WS server accepts socket, sends `{ type: "error", message: "..." }`, then closes it.

---

## WebSocket Agent Protocol

### Connection

```ts
const wsUrl = API_BASE.replace(/^http/, 'ws') + session.wsUrl;
const ws = new WebSocket(wsUrl);
```

On connect the backend fires `run_opening_task()` immediately — agent executes its task then idles.

### Client → Server

```json
{ "type": "message", "text": "..." }
{ "type": "interrupt" }
{ "type": "new_session" }
```

### Server → Client

| `type` | Extra fields | Meaning |
|---|---|---|
| `connected` | `agent`, `cwd` | Socket open, session ready |
| `system` | `model`, `session_id`, `cwd`, `permission_mode` | Session metadata |
| `assistant` | `text` | Agent reply chunk |
| `result` | `duration_ms`, `total_cost_usd`, `num_turns`, `input_tokens`, `output_tokens`, `cache_read_tokens` | End-of-turn summary |
| `turn_complete` | — | Turn finished |
| `interrupted` | — | Interrupt processed |
| `session_reset` | — | `new_session` processed |
| `error` | `message` | Error (socket may close if fatal) |

### State machine

- `thinking = true` on send → cleared by `assistant`, `turn_complete`, `interrupted`, `error`
- `connected = true` on `connected` → cleared on socket `close`
- Reconnect: `ws.close(); setTimeout(connect, 100)`
- **Never use `{#key sessionKey}`** around a chat panel — destroys and recreates, killing the WS subprocess
