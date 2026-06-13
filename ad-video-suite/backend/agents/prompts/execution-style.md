# Execution Style — Task Instructions

Derive the arc ID from the last segment of your cwd path (e.g. `A02R01`).

**On connect, check for existing work first:**
- If `{arc_id}-execution.md` exists in your cwd → **resume run**: read the file and reply with:
  - Selected style and its key constraints (framing, presenter, pacing)
  - What refinements you can do: switch to a different style, adjust framing rules,
    update micro-expression guidance, or regenerate from scratch
  - Wait for instructions — do not regenerate anything automatically.
- Otherwise → **first run**: proceed below.

---

Your cwd is an arc folder (e.g. `A02R01/`). The parent angle folder is available as an
extra directory — read `../A*.md` for the angle brief.

Read:
- `{arc_id}.md` in your cwd — the narrative concept (beats, physical manifestations)
- `../A*.md` in the parent folder — the strategic angle brief

Then propose **2–3 execution style options** ranked by fit for this specific narrative and
angle combination. For each option provide:

- **Style name** — one of the four matrices below, or a named hybrid
- **Why it fits** — one sentence linking the narrative's structure to this style's strengths
- **Key constraints preview** — 2–3 bullet points: framing, presenter type, pacing feel

### Style Matrices (reference, not an enum — hybrids are valid)

**UGC Testimonial**
Smartphone selfie framing. Presenter speaks directly to camera throughout. Eye contact
is sustained, broken only by natural blinks or glances at product. Micro-expressions
drive authenticity: fatigue, hesitation, genuine relief — never performed. Pacing is
conversational with real pauses.

**UGC Review**
Presenter-led voiceover over active product interactions. Camera alternates between
presenter face and hands-on product shots. Emphasis on tactile authenticity — how the
product feels and responds. Pacing follows product interaction rhythm.

**Hybrid UGC + Product Showcase**
Hook with direct-to-camera presenter (organic, selfie energy) → mid-section shifts to
studio-grade product close-ups → presenter returns for closing conversion prompt. Dual
energy: human trust at open and close, product proof in the middle.

**Product Showcase / Demo**
Zero on-camera presenter. Pure macro lens product footage with motion graphics and
text overlays as the sole communication layer. High reliance on physical feature proof
and kinetic typography. Pacing is tighter, cut-driven.

---

Present the options clearly and wait for the user to select one. After selection, write
`{arc_id}-execution.md` in your cwd with the structure below.

---

## Output: `{arc_id}-execution.md`

```
# Execution Style — {arc_id}

**Style:** [Style name]
**Has Presenter:** [true / false]

## Framing
[Camera distance, angle, device feel — one sentence]

## Eye Contact
[Rules for when to hold, break, or avoid eye contact]

## Micro-Expressions & Body Language
[Specific cues: what the presenter's face and body do at each narrative beat — reference
the beat names from the narrative concept doc]

## Pacing
[Rhythm, pause points, speech register — conversational / voiceover / dynamic / tight]

## Downstream Notes
- **Script:** [tone, register, first vs. third person]
- **Character:** [presenter type if applicable, or "no presenter — skip character generation"]
- **Hooks:** [delivery mode — direct-to-camera / voiceover / action-led]
- **Image generation:** [lighting style, shot type preferences]
```

<!-- Output: {cwd}/{arc_id}-execution.md -->
<!-- add_dirs: [".."] provides access to the parent angle folder -->
