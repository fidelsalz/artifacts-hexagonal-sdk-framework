# How to Add New Agents

This guide covers everything needed to add an agent — or a whole new section — without reading
the router, config loader, or conversation session code. All routing is data-driven; you only
touch config and prompt files.

---

## The 3-file checklist

Every new agent touches exactly three places:

| # | File | What to do |
|---|---|---|
| 1 | `agents/agents-config.template.yaml` | Add the agent entry |
| 2 | `agents/prompts/<agent-id>.md` | Write the prompt |
| 3 | `core/campaigns.py` | Add new section folders (only when creating a new section) |

Then, for any **existing** campaign: manually add the agent to its `agents/agents-config.yaml`
and copy the prompt file into its `agents/prompts/`. New campaigns pick everything up automatically.

---

## Step 1 — Add the agent entry to the template

Open `agents/agents-config.template.yaml` and add a block under `team.agents`.

### Minimal entry

```yaml
    my-agent:
      id:              "my-agent"
      name:            "My Agent"
      role:            "One-line description of what it does"
      comm_type:       ws
      cwd_pattern:     '[A-Z]{3}$'
      prompt_file:     "{campaign_dir}/agents/prompts/my-agent.md"
      basic_prompt:    *basic_prompt
      model:           *model
      permission_mode: *dontask_mode
      allowed_tools:   *write_tools
      max_concurrent:  1
      sections:        [MYSECTION]
```

### Field reference

| Field | What it does | Notes |
|---|---|---|
| `id` | Unique key used in URLs and config lookups | kebab-case, no spaces |
| `comm_type` | Always `ws` | All agents are WebSocket |
| `cwd_pattern` | Regex matched against the **last folder segment** the user clicks | Uses `re.search()` — anchor with `^`/`$` to avoid accidental matches |
| `sections` | 3-letter section codes where this agent appears | Empty = appears everywhere |
| `add_dirs` | Extra folders the agent can read/write | Relative to `cwd` at session start |
| `basic_prompt` | First message sent to the agent on connect | Use `*basic_prompt` for autonomous agents; write custom text for conversational agents |
| `model` | `*model` (Sonnet 4.6) or `*lightmodel` (Haiku 4.5) | Use lightmodel for fast, mechanical tasks |
| `allowed_tools` | Use `*write_tools` (Read/Write/Edit/Grep/Glob) or list explicitly | Add `Bash` and `WebFetch` when the agent needs to download or fetch URLs |

### `cwd_pattern` — common patterns and anchoring rules

`re.search()` is used, **not** `re.fullmatch()`. Without anchors, short patterns match inside
longer strings — `[A-Z]{2}$` matches `IMG`, `INT`, `SCE` (all end in two caps). Use `^` to pin
the start.

| Folder type | Pattern | Example match |
|---|---|---|
| 3-letter section folder | `[A-Z]{3}$` | `INT`, `PRD`, `IMG` |
| 2-letter platform subfolder | `^[A-Z]{2}$` | `ML`, `FB` (not `INT`) |
| Angle folder | `A\d+$` | `A01`, `A12` |
| Arc folder | `A\d+R\d+$` | `A01R01` |
| Hook folder | `A\d+R\d+H\d+$` | `A01R01H01` |
| Named subfolder | `script$` | `script` |

### `add_dirs` — cross-folder access

Agents are confined to their `cwd`. `add_dirs` is the only way to grant access to files outside it.
Paths are relative to `cwd` and resolved to absolute paths at session start.

```yaml
add_dirs: ["../../PRD"]   # from IMG/ML/ → campaign root → PRD/
add_dirs: ["../script"]   # from scene-specs/ → sibling script/
add_dirs: [".."]          # parent folder
```

Always document which files the agent reads from `add_dirs` in its prompt file.
If the agent must not modify those files, say so explicitly in the prompt.

### `basic_prompt` — autonomous vs conversational

**Autonomous** (runs the task immediately, waits for refinements):
```yaml
basic_prompt: *basic_prompt
```

**Conversational** (greets user, asks questions, builds output interactively):
```yaml
basic_prompt: >-
  Your working directory is {cwd}.
  Read your instructions at {prompt_file}.
  Begin the conversation immediately — [describe opening move].
```

`{cwd}` and `{prompt_file}` are the only supported placeholders; both are injected at session start.

---

## Step 2 — Write the prompt file

Create `agents/prompts/<agent-id>.md`. This file is the agent's task specification.

### Recommended structure

```markdown
# Agent Name — Task Instructions

Your cwd is [describe what folder this is].
[If add_dirs are used]: [Folder X] is available as an extra directory. Do NOT modify files there.

---

## Mission
[What the agent is responsible for. One paragraph.]

## Inputs
[List files the agent reads, with paths relative to cwd or add_dirs.]

## Steps
[Numbered steps the agent should follow.]

## Outputs
[List output files with paths, schemas, and examples.]

<!-- Inputs:  [summary] -->
<!-- Output: [summary] -->
```

The HTML comments at the bottom serve as a quick machine-readable summary — keep them.

---

## Step 3 — Add section folders to the scaffold (new sections only)

If you are creating a **new section** that should exist in every new campaign, add it to
`core/campaigns.py`:

```python
# Section folders
for section in ("PRD", "IMG", "INT", "SCE", "NEWSECTION"):
    (campaign_dir / section).mkdir(exist_ok=True)

# Add any required subfolders
(campaign_dir / "NEWSECTION" / "subfolder").mkdir(exist_ok=True)
```

If agents work inside a platform subfolder (like `IMG/ML/`), pre-create that subfolder here too
so it appears in the tree without the user having to create it manually.

---

## Step 4 — Apply to existing campaigns (manual)

New campaigns get everything automatically. For existing campaigns:

1. **Copy the prompt file** into the campaign's `agents/prompts/`:
   ```bash
   cp backend/agents/prompts/my-agent.md /path/to/campaigns/C001/agents/prompts/
   ```

2. **Add the agent block** to the campaign's `agents/agents-config.yaml`.
   Replace `{campaign_dir}` with the absolute path to the campaign folder.
   Example entry (adapt from the template):
   ```yaml
   my-agent:
     id: my-agent
     name: My Agent
     ...
     prompt_file: /absolute/path/to/C001/agents/prompts/my-agent.md
     sections: [MYSECTION]
   ```

3. **Create any missing folders** in the campaign:
   ```bash
   mkdir -p /path/to/campaigns/C001/NEWSECTION/subfolder
   ```

---

## Step 5 — Higgsfield agents (extra wiring)

If the agent calls Higgsfield MCP tools, two things are required:

### 5a — Add Higgsfield tools to `allowed_tools`
```yaml
allowed_tools:
  - Read
  - Write
  - Bash
  - mcp__claude_ai_higgsfield__generate_image
  - mcp__claude_ai_higgsfield__job_status
  - mcp__claude_ai_higgsfield__job_display
  - mcp__claude_ai_higgsfield__models_explore
  - mcp__claude_ai_higgsfield__balance
  - mcp__claude_ai_higgsfield__media_upload
  - mcp__claude_ai_higgsfield__media_confirm
  # add others as needed
```

### 5b — Add an `mcp_overrides` entry (required — without this, Higgsfield won't load)
At the bottom of `agents-config.template.yaml`, under the top-level `mcp_overrides` key:

```yaml
mcp_overrides:
  my-agent:
    strict_mcp_config: true
    mcp_servers:
      "claude.ai higgsfield":
        type: http
        url: "https://mcp.higgsfield.ai/mcp"
```

Do the same in the campaign's `agents/agents-config.yaml`.

---

## Common patterns

### Pattern A — Section-level agent (works at the section folder itself)

```
C001/MYSEC/          ← user clicks here
```

```yaml
cwd_pattern: '[A-Z]{3}$'
sections:    [MYSEC]
add_dirs:    []
```

The agent's cwd is `MYSEC/`. It reads and writes directly there.

---

### Pattern B — Named subfolder agent (each run in its own subfolder)

```
C001/INT/A01R01H01/   ← user clicks here
  script/             ← script agent writes here
  scene-specs/        ← scene-specs agent reads script/, writes here
```

```yaml
# script agent
cwd_pattern: 'A\d+R\d+H\d+$'
sections:    [SCE]
add_dirs:    []

# scene-specs agent
cwd_pattern: 'A\d+R\d+H\d+$'
sections:    [SCE]
add_dirs:    ["script"]    # relative to same cwd — grants read of the sibling folder
```

When multiple agents match the same folder, the UI shows a disambiguation picker.

---

### Pattern C — Platform subfolder agent (section → platform → agent)

```
C001/IMG/ML/          ← user clicks here; agents work here
```

```yaml
cwd_pattern: '^[A-Z]{2}$'   # anchored: matches ML, FB, TT but NOT IMG/INT/SCE
sections:    [IMG]
add_dirs:    ['../../PRD']   # from IMG/ML/ up two levels → C001/ → PRD/
```

Adding a new platform (e.g. `FB`) requires only:
1. Pre-create `IMG/FB/` in `core/campaigns.py`
2. The same agents appear automatically (they match any 2-letter folder under `IMG/`)

---

## Cross-section promotion endpoints

Two endpoints copy INT intelligence files into downstream section folders so agents have
focused, pre-digested context. Both are idempotent — existing files are skipped, not overwritten.

### `POST /api/promote-hook` — INT hook → SCE

Seeds files from an `A##R##H##` hook folder into a flat `SCE/{hook_id}/` folder.
Required before launching any SCE agent (SCE agents have no `add_dirs` to INT).

**Request:** `{ "path": "/abs/path/to/C001/INT/A01/A01R01/A01R01H01" }`

**Files copied:**
| Source (INT) | Destination (SCE/{hook_id}/) |
|---|---|
| `INT/research.md` | `research.md` |
| `INT/A##/A##.md` | `A##.md` |
| `INT/A##/A##R##/A##R##.md` | `A##R##.md` |
| `INT/A##/A##R##/timing-blueprint.json` | `timing-blueprint.json` |
| `INT/A##/A##R##/A##R##H##/A##R##H##.md` | `A##R##H##.md` |

**Response:** `{ sce_path, files_copied, files_skipped, files_missing }`

---

### `POST /api/promote-arc` — INT arc → IMG platform

Seeds files from an `A##R##` arc folder into a flat `IMG/{platform}/` folder.
Optional but recommended before running `ml-planner` — pins which arc to use and gives the
agent direct access to angle, arc, and all hook briefs without scanning all of INT.

**Request:** `{ "path": "/abs/path/to/C001/INT/A01/A01R01", "platform": "ML" }`

`platform` must be 2–3 uppercase letters (e.g. `"ML"`, `"FB"`). Defaults to `"ML"` in the UI.

**Files copied:**
| Source (INT) | Destination (IMG/{platform}/) |
|---|---|
| `INT/research.md` | `research.md` |
| `INT/A##/A##.md` | `A##.md` |
| `INT/A##/A##R##/A##R##.md` | `A##R##.md` |
| `INT/A##/A##R##/hooks-index.md` | `hooks-index.md` |
| `INT/A##/A##R##/A##R##H##/A##R##H##.md` (all hooks) | `A##R##H##.md` (one per hook) |

Hook files are discovered by enumerating subdirs — however many hooks exist are copied.

**Response:** `{ img_path, files_copied, files_skipped, files_missing }`

---

## Verification checklist

After adding a new agent:

- [ ] Backend running: `curl http://localhost:8011/api/tree` — confirm new folder appears in the tree
- [ ] Agent listed: `curl "http://localhost:8011/api/infer-agent?path=/campaigns/C001/MYSEC&campaign=C001"` — confirm agent shows up
- [ ] WS connects: open a WS to the agent's URL and confirm `basic_prompt` fires correctly
- [ ] Higgsfield only: confirm the MCP server loads by checking that Higgsfield tool calls succeed (not just that the session opens)
