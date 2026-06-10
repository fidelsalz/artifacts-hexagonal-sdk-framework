# SDK Hex Artifact Suite

A web UI for orchestrating a team of Claude SDK agents that build software using the **hexagonal architecture** pattern. Each agent owns one layer of the architecture and runs autonomously inside Claude Code; the UI lets you trigger, monitor, and chat with them.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python · FastAPI · `claude_agent_sdk` |
| Frontend | SvelteKit · Svelte 5 runes · Tailwind CSS v4 · bits-ui |

## Quick start

```bash
# Backend (port 8010)
cd backend && uvicorn main:app --port 8010 --reload

# Frontend (port 5173)
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173/agents`.

## The agent team

Agents run in this pipeline order, each reading outputs from the previous stage:

| # | Agent | Type | Role |
|---|---|---|---|
| 0 | **Human Assistant** | WS chat | Gathers and clarifies requirements; writes output to `0-human/out/` |
| 1 | **Contracts Writer** | WS chat | Produces ports spec, domain exceptions, execution policy, completeness docs |
| 2 | **Hexagon** | SSE run | Implements domain entities, use cases, business logic |
| 3 | **Ports** | SSE run | Defines input/output port interfaces |
| 4 | **Adapters** | SSE run | Implements adapters connecting ports to external systems |
| 5 | **Infra** | SSE run | DB, messaging, logging, external service clients |

Each SSE coding agent also has a paired **validator** that checks its output. Validators can run automatically after their parent agent finishes (`auto` mode) or be triggered manually.

## Case directory layout

Each run targets a **case directory** (set in `backend/agents/agents-config.yaml` → `config.case_dir`). The convention inside a case:

```
case-NNN/
  0-human/
    prompt/       ← agent reads its instructions here
    in/           ← contract files copied from upstream agents
    out/          ← agent writes its deliverables here
    work/         ← scratch space
  1-contracts-writer/
  2-hexagon/
  ...
```

Before each SSE run the backend automatically:
1. Copies declared contract files from upstream `out/` dirs into the agent's `in/`
2. Restores the `coding_dir` from the latest `.tar.gz` snapshot (rollback)
3. Clears the agent's `out/` for fresh output

## Configuration

All agents are configured in a single file: `backend/agents/agents-config.yaml`.

Change `config.base_path` (and derived `code_base` / `case_dir`) at the top to point at your project. Everything else — model, permission mode, tools, prompts — is set per agent and shared via YAML anchors.

The config is **reloaded on every request** so edits take effect without restarting the backend.

## API

FastAPI auto-generates interactive docs at `http://localhost:8010/docs`.

Key endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/agents/{id}/stream` | Run agent, stream SSE events |
| `WS` | `/ws/agents/{id}/chat` | Multi-turn conversation session |
| `GET` | `/api/agents/{id}/paths` | Resolve cwd / coding_dir for an agent |
| `GET` | `/api/files/list?path=…` | Browse filesystem (used by file explorer) |
| `GET` | `/api/files/read?path=…` | Read a file |
| `POST` | `/api/files/write` | Write a file |
