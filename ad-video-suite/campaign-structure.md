# Campaign Folder Structure + I/O Flow

One folder per campaign. All agent runs for a campaign live here.
Set `config.campaign_dir` in `agents-config.yaml` to point at this root.

---

## Runtime Folder Layout

```
campaigns/
└── [product-slug]/
    │
    ├── product/                        ← USER DROPS FILES HERE (read-only for agents)
    │   ├── info.md                     required
    │   ├── specs.md
    │   ├── reviews.md
    │   ├── competitors.md
    │   └── images/
    │
    ├── 00-research/
    │   ├── prompt/research-prompt.md
    │   ├── in/                         ← spread from product/ before run
    │   │   ├── info.md
    │   │   ├── specs.md
    │   │   ├── reviews.md
    │   │   └── competitors.md
    │   └── out/
    │       └── research.md             ✦ primary output
    │
    ├── 01-angles/
    │   ├── prompt/angles-prompt.md
    │   ├── in/
    │   │   └── research.md
    │   └── out/
    │       ├── angle-index.md
    │       ├── A1—[Name]/A1.md
    │       ├── A2—[Name]/A2.md
    │       ├── A3—[Name]/A3.md
    │       ├── A4—[Name]/A4.md
    │       ├── A5—[Name]/A5.md
    │       └── selected-angle.md       ← UI writes this after user picks
    │
    ├── 02-arcs/
    │   ├── prompt/arcs-prompt.md
    │   ├── in/
    │   │   ├── selected-angle.md
    │   │   └── research.md
    │   └── out/
    │       ├── arcs-index.md
    │       ├── A{n}-R1—[Name]/A{n}-R1.md
    │       ├── A{n}-R2—[Name]/A{n}-R2.md
    │       ├── A{n}-R3—[Name]/A{n}-R3.md
    │       └── selected-arc.md         ← UI writes this after user picks
    │
    ├── 03-timing/
    │   ├── prompt/timing-prompt.md
    │   ├── in/
    │   │   └── selected-arc.md
    │   └── out/
    │       └── timing-blueprint.json   ✦ primary output
    │
    ├── 04-hooks/
    │   ├── prompt/hooks-prompt.md
    │   ├── in/
    │   │   ├── selected-angle.md
    │   │   ├── selected-arc.md
    │   │   ├── timing-blueprint.json
    │   │   └── research.md
    │   └── out/
    │       ├── hooks-index.md
    │       ├── A{n}-R{n}-H1—[Name]/A{n}-R{n}-H1.md
    │       ├── A{n}-R{n}-H2—[Name]/A{n}-R{n}-H2.md
    │       ├── A{n}-R{n}-H3—[Name]/A{n}-R{n}-H3.md
    │       ├── A{n}-R{n}-H4—[Name]/A{n}-R{n}-H4.md
    │       ├── A{n}-R{n}-H5—[Name]/A{n}-R{n}-H5.md
    │       └── selected-hook.md        ← UI writes this after user picks
    │
    ├── 05-script/
    │   ├── prompt/script-prompt.md
    │   ├── in/
    │   │   ├── selected-angle.md
    │   │   ├── selected-arc.md
    │   │   ├── timing-blueprint.json
    │   │   ├── selected-hook.md
    │   │   └── research.md
    │   └── out/
    │       ├── script.json             ✦ primary output
    │       └── script-readthrough.md   plain text for quick human review
    │
    ├── 06-scene-specs/
    │   ├── prompt/scene-specs-prompt.md
    │   ├── in/
    │   │   ├── selected-angle.md
    │   │   ├── selected-arc.md
    │   │   ├── timing-blueprint.json
    │   │   ├── script.json
    │   │   └── research.md
    │   └── out/
    │       └── scene-specs.json        ✦ primary output
    │
    ├── 07-shots/                       ─┐ parallel
    │   ├── prompt/shots-prompt.md       │
    │   ├── in/                          │
    │   │   ├── scene-specs.json         │
    │   │   └── assets_manifest.json     │
    │   └── out/                         │
    │       └── shot-list.json           │
    │                                    │
    ├── 08-graphics/                    ─┘ parallel
    │   ├── prompt/graphics-prompt.md
    │   ├── in/
    │   │   ├── scene-specs.json
    │   │   └── script.json
    │   └── out/
    │       └── graphics-plan.json
    │
    └── assets/
        ├── assets_manifest.json        updated after each Higgsfield render
        └── renders/                    generated video clips (named by reuse scope)
            ├── scene_[type]_[desc]_v1.mp4      reuse_potential: universal
            ├── A{n}_[type]_v1.mp4              reuse_potential: angle
            └── A{n}-R{n}-H{n}_[type].mp4       reuse_potential: none
```

---

## I/O Flow

```
product/  ──────────────────────────────────────────────────────────────────────┐
                                                                                 │
[Agent 1 — Research]  ◄──────────────────────────────────────────────────────── ┘
  in:  info.md  specs.md  reviews.md  competitors.md
  out: research.md
                │
                ▼
[Agent 2 — Angles]
  in:  research.md
  out: angle-index.md  A1.md … A5.md
                │
          ★ USER PICKS ANGLE
          UI writes: selected-angle.md
                │
                ▼
[Agent 3 — Arcs]
  in:  selected-angle.md  research.md
  out: arcs-index.md  A{n}-R1.md  A{n}-R2.md  A{n}-R3.md
                │
          ★ USER PICKS ARC
          UI writes: selected-arc.md
                │
                ▼
[Agent 4 — Timing]        ← fires automatically after arc pick, no gate
  in:  selected-arc.md
  out: timing-blueprint.json
                │
                ▼
[Agent 5 — Hooks]
  in:  selected-angle.md  selected-arc.md  timing-blueprint.json  research.md
  out: hooks-index.md  A{n}-R{n}-H1.md … H5.md
                │
          ★ USER PICKS HOOK
          UI writes: selected-hook.md
                │
                ▼
[Agent 6 — Script]
  in:  selected-angle.md  selected-arc.md  timing-blueprint.json
       selected-hook.md  research.md
  out: script.json  script-readthrough.md
                │
          ★ USER APPROVES SCRIPT
                │
                ▼
[Agent 7 — Scene Specs]
  in:  selected-angle.md  selected-arc.md  timing-blueprint.json
       script.json  research.md
  out: scene-specs.json
                │
        ┌───────┴───────┐  (parallel)
        ▼               ▼
[Agent 8 — Shots]   [Agent 9 — Graphics]
  in: scene-specs.json   in: scene-specs.json
      assets_manifest.json   script.json
  out: shot-list.json    out: graphics-plan.json
        └───────┬───────┘
                ▼
        Higgsfield renders  ←── shot-list.json (higgsfield_prompt per shot)
        Remotion composite  ←── graphics-plan.json
        FFmpeg export
        assets_manifest.json updated
```

---

## Pick convention

When a user picks an option, the UI writes the selected content to a **stable filename**
in the source agent's `out/` directory. Downstream agents declare that filename in their
`in_sources` so `spread_inputs` copies it automatically on next run.

| Gate | Stable filename written by UI |
|---|---|
| Angle pick | `01-angles/out/selected-angle.md` |
| Arc pick | `02-arcs/out/selected-arc.md` |
| Hook pick | `04-hooks/out/selected-hook.md` |
| Script approve | (no file written — just unlocks scene-specs) |

---

## Assets manifest

`assets/assets_manifest.json` is a shared resource read by Agent 8 (shots) to identify
clips that can be **reused** instead of re-generated. It is updated outside the agent
pipeline — by the render step or manually after each Higgsfield job completes.

Reuse scope encoded in filename prefix:
- `scene_*` — universal, no product/angle-specific content
- `A{n}_*` — angle-specific, reusable across arcs/hooks of that angle
- `A{n}-R{n}-H{n}_*` — fully specific, one variant only
