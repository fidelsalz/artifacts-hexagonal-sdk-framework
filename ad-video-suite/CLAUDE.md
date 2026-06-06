# CLAUDE.md — Orchestrator

## Scope

This is the orchestrator level. Coordinate cross-cutting changes — API contracts, shared types,
folder conventions, pipeline design. Delegate implementation to the backend or frontend agent.
Do not implement backend or frontend details directly; describe what needs to change and hand off.

## Services

| Service | Directory | Port | Start command |
|---|---|---|---|
| Backend (FastAPI) | `backend/` | 8011 | `cd backend && /home/fidel/.conda/envs/aiprog/bin/python3.12 -m uvicorn main:app --port 8011 --reload` |
| Frontend (SvelteKit) | `frontend/` | 5173 | `cd frontend && npm run dev` |

See `backend/CLAUDE.md` and `frontend/CLAUDE.md` for full details on each subsystem.

## Product Overview

Ad Video Suite produces direct-response video ads and ad images through four sections:

- **PRD (Product)** — collects and structures all product knowledge. Feeds every downstream section. Agents work directly in `PRD/`.
- **IMG (Image Ads)** — generates platform-specific ad images from product knowledge. Each platform gets its own subfolder (`IMG/ML/`, `IMG/FB/`, …). Agents work in the platform subfolder.
- **INT (Intelligence)** — research, angles, arcs, timing, hooks. Pure thinking and planning. Agents work in the campaign folder tree under `INT/`.
- **SCE (Scenification)** — script, scene-specs, shots, graphics, image/video generation. Turns INT output into production-ready assets. Agents work in isolated hook subfolders under `SCE/`.

The folder tree is the pipeline — no forced order, no state machine. The UI exposes the tree; clicking a folder launches the matching agent.

## Sections and Agents

| Section | Subfolder | Agents | Purpose |
|---|---|---|---|
| `PRD/` | — | `product-creator` | Gather product info, create knowledge files |
| `IMG/ML/` | Mercado Livre | `ml-planner`, `ml-creator` | Plan and generate ML ad images |
| `INT/` | — | `research`, `angles` | Audience research + angle strategy |
| `INT/A##/` | — | `arcs` | Emotional arc variants |
| `INT/A##R##/` | — | `timing`, `hooks` | Timing blueprint + hook variants |
| `SCE/A##R##H##/` | — | `script`, `storyboard`, `scene-specs`, `shots`, `image-prompts`, `image-generation`, `video-prompts`, `generated-clips`, `graphics` | Full production pipeline |

## Cross-Cutting Concerns

- **API contract** between frontend and backend is defined by `backend/routers/` — any route change requires coordinating both sides
- **Folder naming convention** (`C###`, `INT`, `SCE`, `PRD`, `IMG`, `ML`, `A##`, `A##R##`, `A##R##H##`) is shared knowledge — changes affect backend routing, frontend display, and campaign folder structure simultaneously
- **Agent config** lives in `backend/agents/agents-config.template.yaml` and is copied per-campaign at creation time — structural changes (new agents, new sections) need both the template and any existing campaign YAMLs updated
- **New section scaffold** is hardcoded in `backend/core/campaigns.py` — adding a new section (e.g. `VID/`) requires updating the folder list there
- **Adding agents**: see `backend/agents/HOW-TO-ADD-AGENTS.md`
