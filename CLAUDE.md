# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (FastAPI — port 8010)
```bash
cd backend && uvicorn main:app --port 8010 --reload
```

### Frontend (SvelteKit — port 5173)
```bash
cd frontend && npm run dev
```

### Frontend checks & tests
```bash
cd frontend
npm run check          # svelte-check type checking
npm run lint           # prettier + eslint
npm run format         # prettier auto-fix
npm run test:unit      # vitest unit tests
npm run test:e2e       # playwright e2e tests
npm run storybook      # component explorer on port 6006
```

## Architecture

This is a **multi-agent orchestration UI** that drives a team of Claude SDK agents building software using hexagonal architecture. The project is a monorepo with `backend/` (Python/FastAPI) and `frontend/` (SvelteKit).

### Agent Communication: Two Modes

All agents are defined in `backend/agents/agents-config.yaml` and have a `comm_type`:

- **`sse` (one-shot)**: Agent runs to completion, streams structured events back via `GET /api/agents/{id}/stream`. Used by coding agents (ports, hexagon, adapters, infra) and their validators.
- **`ws` (interactive)**: Persistent multi-turn session via `WebSocket /ws/agents/{id}/chat`. Used by human-assistant and contracts-writer.

### Backend Data Flow

1. `agents-config.yaml` — single source of truth. Uses `{{ variable }}` placeholders resolved by `agents/config.py` into typed `AgentConfig` / `ValidatorConfig` dataclasses.
2. `agents/__init__.py` → `get_agent(name)` — routes agent IDs to implementations:
   - `CODING_AGENT_IDS` (`ports`, `hexagon`, `adapters`, `infra`) → `CodingAgent(id)` in `agents/coding_agent.py`
   - `VALIDATOR_IDS` → `ValidatorAgent(id)` in `agents/validator_agent.py`
3. `CodingAgent.execute()` chains: `pre_run` (spread inputs, rollback coding dir, clear out/) → `run_stream` (calls `claude_agent_sdk.query()`) → `post_run`.
4. `ConversationSession` in `agents/conversation_agent.py` wraps `ClaudeSDKClient` for multi-turn WS sessions.
5. Routers: `routers/agents.py` (SSE stream + WS), `routers/files.py` (browse/read/write filesystem for FolderExplorer), `routers/basic.py`.

### Pre-run Lifecycle (SSE coding agents)

Before each agent run, three steps happen in `rollback.py`:
- **`spread_inputs`**: copies contract files from upstream agents' `out/` into `{cwd}/in/`
- **`rollback_coding_dir`**: restores `coding_dir` from the latest `*-{foldername}.tar.gz` snapshot in the parent dir, wiping any previous run's changes
- **`clear_out_dir`**: empties `{cwd}/out/` for fresh output

### Frontend State Management

Global state lives in `frontend/src/lib/stores/caseStore.svelte.js` using Svelte 5 `$state`. The `caseState.agents` array holds all agent state (status, messages, changedPaths). State survives tab switches because it's in a module-level `$state`, not component-local.

**Key pattern**: WS conversation panels (`ConversationPanel`) are **always mounted in the DOM** (hidden via CSS `class="hidden"`) so each keeps its live `ClaudeSDKClient` subprocess. Switching tabs never destroys WS sessions. SSE panels are rendered only when active.

### Frontend Components (`frontend/src/lib/components/`)

- `AgentTabPanel` — SSE agent panel (solo, no validator pair)
- `CodingAgentPanel` — SSE agent + validator pair panel with `FolderExplorer` in the right column
- `ConversationPanel` — WS chat panel with `FolderExplorer` in the right column
- `FolderExplorer` — file browser backed by `/api/files/list` and `/api/files/read`; uses `FileEditorModal` to edit files via `/api/files/write`
- `DashboardPanel` — summary of all agents (cost, status)

### Validator Auto-chaining

After an SSE coding agent completes, `caseStore.svelte.js` checks if the paired validator has `mode === 'auto'` and automatically triggers it. The `VALIDATOR_PAIR` map in the store connects agent IDs to their validators.

### Adding a New Agent

1. Add an entry under `team.agents` in `backend/agents/agents-config.yaml`
2. If it's a generic coding agent, add its ID to `CODING_AGENT_IDS` in `backend/agents/__init__.py`; if it has a validator, add to `VALIDATOR_IDS`
3. Add the agent (and validator) to `caseState.agents` in `caseStore.svelte.js`
4. Add a tab entry in `frontend/src/routes/agents/+page.svelte`

### Frontend notes

- Uses Svelte 5 runes (`$state`, `$derived`, `$effect`, `$props`) — not the legacy Options API
- UI components come from `bits-ui` (shadcn-svelte pattern), exported from `src/lib/components/ui/`
- Styling: Tailwind CSS v4, zinc color scale, light theme
- API base URL: `http://localhost:8010` (configured in `src/lib/config.js`, overridable via `VITE_API_BASE_URL`)
- The Svelte MCP server is configured (`.mcp.json`); use `list-sections` then `get-documentation` for Svelte 5 / SvelteKit docs, and `svelte-autofixer` before delivering Svelte code
