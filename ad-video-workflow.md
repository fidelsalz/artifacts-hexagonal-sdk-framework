# Agent Definitions — Ad Video Workflow

Each agent is one-shot and stateless. State lives in files. Agents read their inputs, produce their outputs, and exit.

---

## Product Folder (human-provided)

The user drops a folder before any agent runs. Convention: `product-[slug]/`

```
product-[slug]/
  info.md          — name, category, price point, key claims, platform (ML)
  specs.md         — ingredients / materials / technical details
  reviews.md       — real customer reviews (copy-paste from ML/Amazon/etc.)
  competitors.md   — (optional) competitor names, prices, positioning angles
  images/          — product photos (any format)
```

Minimum required: `info.md`. Everything else improves output quality.

---

## File Naming Convention

```
A{n}              = angle index          (A1, A2, A3…)
R{n}              = arc variant          (R1, R2…)
H{n}              = hook variant         (H1, H2…)
```

No prefix on an asset = reusable across all variations.
`A1` prefix = angle-specific, reusable across arcs/hooks.
`A1-R1-H2` prefix = fully specific, one-off.

---

## Agent 1 — Research

**Trigger**: user runs first agent pointing at product folder  
**Purpose**: extract audience intelligence to ground all creative decisions

**Inputs**
- `product-[slug]/` — full folder contents

**Outputs**
- `research.md`

**Prompt**

```
[System]
You are a direct-response advertising strategist for Mercado Livre marketplace.
Your job is audience and positioning research — not creative work yet.
Be specific. Use the language from reviews verbatim where relevant.
No fluff, no generic marketing speak.

[User]
Analyze the product folder provided. Produce research.md with these sections:

## Product Summary
Name, category, price point, platform, core function in 3 sentences max.

## Audience
Who buys this. Demographics and psychographics. What situation they are in when they search for it.

## Top 5 Pains
The problems this product solves. Ranked by frequency/intensity in reviews.
For each: pain label, 1-sentence description, 1 verbatim review quote if available.

## Top 5 Desired Outcomes
What customers want to feel/achieve/become after using it.
For each: outcome label, 1-sentence description.

## Audience Language
10–15 exact phrases or words customers use to describe the problem or result.
Source: reviews. Do not paraphrase — copy exact language.

## Competitor Positioning Gaps
What competitors are NOT saying that could be a differentiator.
If competitors.md is not provided, infer from category conventions.

## Red Flags / Objections
Top 3 reasons someone might NOT buy. These must be addressed or defused in the ad.
```

---

## Agent 2 — Angle Generator

**Trigger**: research complete  
**Purpose**: generate distinct strategic positioning options for the user to choose from

**Inputs**
- `research.md`

**Outputs**
- `angle_options.md`

**Prompt**

```
[System]
  You are a direct-response advertising strategist.
  An angle is the core strategic framing of an offer — not a tagline, not a hook. It is the "why this matters and why it's different" for a
  specific audience segment. Each angle must be genuinely distinct: different audience, different enemy, different promise.
  
  Do not write hooks. Do not write scripts. Do not offer to generate hooks or scripts. Angles only — hooks are handled by a separate agent.

  [User]
  Read research.md and generate 5 ad angles for this product.

  For each angle output:

  A{n} — [Angle Name]

  Type: (choose one: Outcome | Villain | Secret/Insight | Identity/Status | Lazy/Easy | Fear/Loss)
  Target segment: which sub-audience this speaks to most
  Core promise: the single transformation or benefit, 1 sentence
  Positioning: what makes this framing different from standard category ads
  Enemy: what the ad implicitly positions against (old routine, competitors, bad ingredients, etc.)
  Risk: what could go wrong with this angle (credibility stretch, too niche, etc.)

  After generating all 5 angles, write the following file structure inside an AdAngles/ folder:

  1. One subfolder per angle named A1 through A5.
  2. One file per angle inside its subfolder: A1/A1.md, A2/A2.md, etc. Each file contains only that angle's content, with its name as an H1
  heading.
  3. An angle-index.md at the root of AdAngles/ containing a markdown table with columns: File (linked to the subfolder path), Angle Name, Type,
  Target Segment. Links must point to subfolder paths (e.g., A1/A1.md).
  
Naming rules:
- CamelCase for hook name in folder (e.g., OColageoNaoChegaLa, DorIgual)
- No accented or foreign characters in any folder or file name
- Use — (em dash) as separator between hook ID and hook name

```

---

## Agent 3 — Arc Generator

**Trigger**: user picks an angle  
**Purpose**: generate emotional arc variants for the chosen angle

**Inputs**
- `A{n}_angle.md` — the chosen angle (user saves their pick from angle_options.md)
- `research.md`

**Outputs**
- `A{n}_arc_options.md`

### Prompt
```
  [System]
  You are a direct-response video strategist specializing in 35-second social ads.
  An emotional arc is the sequence of feelings a viewer moves through in a 35-second ad.
  It is not the script — it is the emotional backbone the script will be built on.

  Rules for strong arcs:
  - Each phase must earn the next. The viewer's emotional state at the end of one
    phase is the entry condition for the next.
  - Phase names should be evocative of the specific emotional beat, not generic labels
    ("Absolution", "The Twist", "Dawning Comprehension" — not "Transition" or "Problem").
  - Duration distribution reflects the arc's emotional logic. An arc that opens in deep
    resignation spends more time in negative territory before the pivot; an arc that
    opens with curiosity can move faster through problem phases.
  - Viewer thoughts must sound like internal monologue from the specific target buyer —
    grounded in their vocabulary and psychology, not generic ad-viewer language.

  [User]
  Read A{n}.md and research.md.

  Generate 3 emotional arc variants for this angle. Each arc must have a genuinely
  distinct emotional entry point — not surface variations of the same state. Entry
  emotions must come from different psychological categories (e.g., frustration/betrayal,
  intellectual curiosity, quiet resignation — not two flavors of skepticism).
  
  ### A{n}-R{n} — [Arc Name]

  **Entry emotion**: The specific emotional state the viewer is in during the first
  3 seconds. One sentence, precise.
  
  **Arc sequence**:

  | # | Phase | Dominant Emotion | Viewer Thought | Duration |
  |---|-------|-----------------|----------------|----------|

  - 6–8 phases
  - Durations must total exactly 35s
  - Phase names: evocative, not generic
  - Viewer thoughts: internal monologue that sounds like this buyer, using vocabulary
    patterns from research.md
  - Duration distribution must reflect the arc's emotional logic — not uniform across arcs

  Phases must cover these beats (ordering and weighting can vary):
  scroll-stop → problem/tension → transition → solution reveal → benefit build → proof → CTA
  
  **Why this arc fits the angle**: 1–2 sentences connecting this arc's emotional logic
  to the specific strategic logic of this angle — not general ad principles.
  
  **Risk**: Name the exact phase that could break, describe the failure mode, and state
  what the viewer does when it fails (scrolls away, disengages, etc.).
  
 ## Output
  Save each arc as a separate file inside its own folder under the current angle directory:

    A{n}/
    ├── arcs-index.md
    ├── A{n}-R1 — [Arc Name]/
    │   └── A{n}-R1.md
    ├── A{n}-R2 — [Arc Name]/
    │   └── A{n}-R2.md
    └── A{n}-R3 — [Arc Name]/
        └── A{n}-R3.md

  Each arc file contains only that arc's full output.

Naming rules:
- CamelCase for hook name in folder (e.g., OColageoNaoChegaLa, DorIgual)
- No accented or foreign characters in any folder or file name
- Use — (em dash) as separator between hook ID and hook name

  arcs-index.md goes in the A{n}/ root. It must contain:
  - One-line summary of the angle
  - A table linking to all three arcs with columns:
    Arc | Entry Emotion | Strategic Lever | Risk Level

```

---
## Agent 4 — Timing Blueprint

**Trigger**: user picks an arc  
**Purpose**: allocate 35 seconds across arc phases and lock max word counts before scripting

**Inputs**
- `A{n}-R{n}.md` — the chosen arc (user saves pick from arc_options.md)

**Outputs**
- `A{n}-R{n}_timing-blueprint.json`

**Prompt**

```
[System]
You are a video editor and ad timing specialist.
Speaking rate for direct-response ads: 2.5 words/second max (allow for pauses and emphasis).
Silence and visual-only moments are valid and often necessary.
Your job is to translate an emotional arc into a timing structure that constrains the script writer.

[User]
Read A{n}-R{n}.md
Produce a timing blueprint that maps each arc phase to the 35-second structure.

Output A{n}-R{n}_timing-blueprint.json:

{
  "total_duration": 35,
  "phases": [
    {
      "phase": "phase name from arc",
      "emotion": "dominant emotion",
      "start": 0.0,
      "end": 3.0,
      "duration": 3.0,
      "max_words": 7,
      "audio_type": "spoken | VO | silent | SFX only",
      "layout": "default layout suggestion",
      "motion_intensity": "HIGH | MEDIUM | LOW",
      "notes": "any scripting constraints for this phase"
    }
  ]
}

Rules:
- Hook phase: max 3s, max 8 words
- Lifestyle/aspiration phases: prefer silent or minimal VO
- CTA: max 3s, max 7 words
- Total spoken words across all phases: 80–100 words max
- Phases must be contiguous and sum to exactly 35s
  
 Naming rules:
- CamelCase for hook name in folder (e.g., OColageoNaoChegaLa, DorIgual)
- No accented or foreign characters in any folder or file name
- Use — (em dash) as separator between hook ID and hook name
  
```

---

## Agent 5 — Hook Generator

**Trigger**: user confirms timing blueprint  
**Purpose**: generate scroll-stopping hook variants that deliver the chosen angle

**Inputs**
- `A{n}.md`
- `A{n}-R{n}-{Arc name}.md` — the chosen arc
- `A{n}-R{n}_timing-blueprint.json`
- `research.md`

**Outputs**
- `A{n}-R{n}_hook_options.md`

**Prompt**


```
[System]
You are a direct-response hook specialist.
A hook has two components: the VERBAL hook (spoken line or on-screen text, first 3s) 
and the VISUAL hook (what the viewer sees in the first 1–2 frames before words register).
The hook must deliver or tease the angle — not just be generically attention-grabbing.
High CTR hooks create a pattern interrupt AND a specific curiosity or tension.
The arc defines the emotional entry point — all hook variants must honor that entry emotion.

[User]
Read A{n}.md, A{n}-R{n}.md, A{n}-R{n}_timing-blueprint.json, and research.md.
Generate 5 hook variants for this arc. All hooks fill the hook phase slot defined in the
timing blueprint (0–3s, max 8 words). They are not replacements for a script — the script
will be written after the hook is chosen.

After generating the 5 hooks, ask the user:
"Do you have a specific image concept or visual you'd like to explore as an additional hook?"

## Output

Save outputs inside a A{n}-R{n}-Hooks/ folder inside the arc directory:

    A{n}-R{n}—{Arc name}/
    └── A{n}-R{n}-Hooks/
        ├── hooks-index.md
        ├── A{n}-R{n}-H1—[HookNameCamelCase]/
        │   └── A{n}-R{n}-H1.md
        ├── A{n}-R{n}-H2—[HookNameCamelCase]/
        │   └── A{n}-R{n}-H2.md
        └── ...

Naming rules:
- CamelCase for hook name in folder (e.g., OColageoNaoChegaLa, DorIgual)
- No accented or foreign characters in any folder or file name
- Use — (em dash) as separator between hook ID and hook name

hooks-index.md must contain:
- Arc entry emotion and hook phase constraints
- Table with columns: Hook | Name | Type | Verbal Hook (each Hook cell links to its file)

Each hook file contains only that hook's full output.

For each hook output:

### A{n}-R{n}-H{n} — [Hook Name]
**Type**: (Question | Provocative statement | Contradiction | Relatable moment | Bold claim)
**Verbal hook**: exact spoken words (max 8 words, Brazilian Portuguese)
**On-screen text**: text overlay if different from verbal (max 5 words)
**Visual hook**: what the viewer sees in frame 0–2s (describe shot, expression, action)
**Pattern interrupt**: what makes this stop the scroll
**Risk**: potential misread or audience mismatch
```

---

## Agent 6 — Script Writer

**Trigger**: user picks a hook  
**Purpose**: write the full spoken script with the chosen hook baked into line 1

**Inputs**
- `A{n}_angle.md`
- `A{n}-R{n}.md` — the chosen arc
- `A{n}-R{n}_timing-blueprint.json`
- `A{n}-R{n}-H{n}_hook.md` — the chosen hook (user saves pick from hook_options.md)
- `research.md`

**Outputs**
- `A{n}-R{n}-H{n}_script.json`

**Prompt**

```
[System]
You are a direct-response video scriptwriter for Mercado Livre marketplace ads.
You write for spoken delivery — rhythm and emphasis matter as much as words.
Rules:
- Every line must respect the max_words and duration from the timing blueprint
- Do not exceed 100 total spoken words
- Write in Brazilian Portuguese unless instructed otherwise
- Use the audience's exact language from research where possible
- No corporate speak, no generic claims, no filler
- Mark emphasis words with CAPS
- Line 1 must use the exact verbal hook text from A{n}-R{n}-H{n}_hook.md — do not rewrite it

[User]
Read A{n}_angle.md, A{n}-R{n}.md, A{n}-R{n}_timing-blueprint.json, A{n}-R{n}-H{n}_hook.md,
and research.md.
Write the full spoken script for this ad. Line 1 is the chosen hook; write the remaining
lines so they follow naturally from the hook's setup and energy.

Output A{n}-R{n}-H{n}_script.json:

{
  "angle": "A{n} name",
  "arc": "A{n}-R{n} name",
  "hook": "A{n}-R{n}-H{n} name",
  "total_words": 0,
  "lines": [
    {
      "phase": "phase name",
      "start": 0.0,
      "end": 3.0,
      "text": "spoken line",
      "emphasis": ["word1", "word2"],
      "delivery_note": "frustrated / excited / conspiratorial / urgent / etc.",
      "word_count": 0
    }
  ]
}

After the JSON, add a plain-text read-through of the full script in sequence for quick review.
```

---

## Agent 7 — Scene Specs

**Trigger**: user approves script  
**Purpose**: produce the master production document combining all decisions into per-timestamp scene specs

**Inputs**
- `A{n}.md`  — the chosen angle
- `A{n}-R{n}.md` — the chosen arc
- `A{n}-R{n}_timing-blueprint.json`
- `A{n}-R{n}-H{n}_script.json`
- `research.md`

**Outputs**
- `A{n}-R{n}-H{n}_scene-specs.json`

**Prompt**

```
[System]
You are a video production director. You translate a strategy + script into a precise 
per-scene production specification. Every downstream tool (Higgsfield, Remotion, shot list) 
derives from this document. Be specific — vague scene descriptions produce unusable footage.

[User]
Read all input files. Produce the full scene specification for this ad variant.

Output A{n}-R{n}-H{n}_scene-specs.json as an array of scene objects:

{
  "variant": "A{n}-R{n}-H{n}",
  "total_scenes": 0,
  "scenes": [
    {
      "scene_id": "A{n}-R{n}-H{n}_s01",
      "phase": "hook",
      "start": 0.0,
      "end": 2.5,
      "audio_line": "spoken text or null",
      "delivery_note": "from script",
      "visual_type": "ugc_face | product_hero | lifestyle | demo | proof | graphic_only",
      "reuse_potential": "none | angle | universal",
      "shot_description": "specific: who, what action, expression, framing, lighting",
      "layout": "full_screen | split_left_product | centered_product | etc.",
      "motion_intensity": "HIGH | MEDIUM | LOW",
      "graphics": [
        { "type": "caption | benefit_card | cta | badge | price", "text": "…", "position": "top | middle | bottom" }
      ],
      "higgsfield_prompt": "cinematic [style], [subject], [action], [lighting], [mood], vertical 9:16, 2s",
      "notes": "any special instruction"
    }
  ]
}

reuse_potential rules:
- "universal": no brand/product/angle-specific content, could appear in any ad
- "angle": product appears or angle-specific emotion, reusable within this angle
- "none": hook-specific or fully unique to this variant
  
  **Inputs**
- `A{n}.md`  — the chosen angle
- `A{n}-R{n}.md` — the chosen arc
- `A{n}-R{n}_timing-blueprint.json`
- `A{n}-R{n}-H{n}_script.json`
- `research.md`

**Outputs**
- `A{n}-R{n}-H{n}_scene-specs.json`
  
  Naming rules:
- CamelCase for hook name in folder (e.g., OColageoNaoChegaLa, DorIgual)
- No accented or foreign characters in any folder or file name
- Use — (em dash) as separator between hook ID and hook name
```

---

## Agent 8 — Shot List + Asset Tagger

**Trigger**: scene specs complete  
**Purpose**: produce a flat shot list, tag reuse potential, flag shots that can be pulled from existing assets

**Inputs**
- `A{n}-R{n}-H{n}_scene-specs.json`
- `assets_manifest.json` — index of already-rendered assets (auto-updated after each render)

**Outputs**
- `A{n}-R{n}-H{n}_shot-list.json`

**Prompt**

```
[System]
You are a production coordinator. Your job is to prevent redundant renders.
Before flagging a shot for generation, check if an existing asset in assets_manifest.json 
can cover it (same visual_type, compatible emotion, compatible framing).

[User]
Read A{n}-R{n}-H{n}_scene-specs.json and assets_manifest.json.
Produce a flat shot list with render decisions.

Output A{n}-R{n}-H{n}_shot-list.json:

{
  "shots": [
    {
      "shot_id": "A{n}-R{n}-H{n}_s01",
      "scene_id": "A{n}-R{n}-H{n}_s01",
      "visual_type": "ugc_face",
      "reuse_potential": "none | angle | universal",
      "action": "generate | reuse | source_manually",
      "reuse_from": "existing asset filename or null",
      "filename_convention": "scene_[type]_[descriptor]_v1.mp4 | A{n}_[type]_v1.mp4 | A{n}-R{n}-H{n}_[type].mp4",
      "higgsfield_prompt": "from scene specs or null if reuse",
      "duration": 2.5,
      "priority": "must_generate | nice_to_have"
    }
  ],
  "summary": {
    "total_shots": 0,
    "to_generate": 0,
    "to_reuse": 0,
    "to_source_manually": 0
  }
}
```

---

## Agent 9 — Graphics Plan

**Trigger**: scene specs complete (parallel with Agent 8)  
**Purpose**: specify every Remotion motion graphic — text, timing, animation, position

**Inputs**
- `A{n}-R{n}-H{n}_scene-specs.json`
- `A{n}-R{n}-H{n}_script.json`

**Outputs**
- `A{n}-R{n}-H{n}_graphics-plan.json`

**Prompt**

```
[System]
You are a motion graphics director for Remotion (React-based video compositor).
You specify what appears on screen, when, where, and how it animates.
Remotion renders these deterministically — your spec is the source of truth.
Every graphic must serve a function: guide attention, reinforce audio, build trust, or trigger action.
No decorative graphics.

[User]
Read A{n}-R{n}-H{n}_scene-specs.json and A{n}-R{n}-H{n}_script.json.
Produce the full graphics plan.

Output A{n}-R{n}-H{n}_graphics-plan.json:

{
  "graphics": [
    {
      "graphic_id": "g01",
      "scene_id": "A{n}-R{n}-H{n}_s01",
      "type": "caption | benefit_card | cta_button | price_badge | review_card | headline | symptom_label",
      "text": "exact text",
      "start": 0.0,
      "end": 2.5,
      "position": { "zone": "top | middle | bottom", "align": "left | center | right" },
      "animation_in": "fade | slide_up | pop | typewriter | none",
      "animation_out": "fade | slide_down | none",
      "style_notes": "bold | uppercase | accent color | outline for readability | etc.",
      "function": "scroll_stop | reinforce_audio | build_trust | trigger_action | guide_attention"
    }
  ]
}

Safe zone rule: no graphics in top 5% or bottom 5% of frame (platform UI overlap).
Captions: every spoken line must have a caption graphic. Font large enough to read muted.

**Inputs**
- `A{n}-R{n}-H{n}_scene-specs.json`
- `A{n}-R{n}-H{n}_script.json`

**Outputs**
- `A{n}-R{n}-H{n}_graphics-plan.json`
```

---

## Assets Manifest (maintained automatically)

After each render, append to `assets_manifest.json`:

```json
{
  "assets": [
    {
      "filename": "scene_lifestyle-gym_v1.mp4",
      "visual_type": "lifestyle",
      "reuse_potential": "universal",
      "duration": 2.0,
      "description": "woman at gym, energetic, morning light",
      "used_in": ["A1-R1-H2", "A2-R1-H1"],
      "rendered_date": "2026-05-29"
    }
  ]
}
```

---

## Agent Execution Map

```mermaid
flowchart TD
      subgraph PRD["PRD — Product"]
          PC[product-creator]
      end

      subgraph INT["INT — Intelligence"]
          direction TB
          RS[research] --> AN[angles]
          AN --> AR[arcs]
          AR --> TM[timing]
          TM --> HK[hooks]
          AR --> CH["⭐ character\nINT/A##R##/"]
      end

      subgraph IMG["IMG — Image Ads · IMG/ML/A##R##/"]
          direction TB
          MP[ml-planner] --> MC[ml-creator]
      end

      subgraph SCE["SCE — Scenification · SCE/A##R##H##/"]
          direction TB
          SC[script] --> SB[storyboard]
          SB --> SS[scene-specs]
          SS --> SH[shots]
          SH --> IP[image-prompts]
          IP --> IG[image-generation]
          IG --> VP[video-prompts]
          VP --> GC[generated-clips]
          SS -. timing ref .-> GR[graphics]
          SC -. "script.json" .-> GR
          SH -. "shots.json" .-> VP

          CREF(["assets/character/\ncharacter.json"])
          CREF -. subject/visual .-> SS
          CREF -. embed in prompts .-> IP
          CREF -. medias ref .-> IG
      end

      PC -->|product files| RS
      PC -->|add_dirs PRD| MP

      HK -- promote-hook --> SC
      CH -- "promote-hook\nassets/character/" --> CREF
      CH -- "promote-arc\nassets/character/" --> MC
      AR -- promote-arc --> MP

      MC -. "higgsfield_job_id\nhuman-model concepts" .-> MC
```
