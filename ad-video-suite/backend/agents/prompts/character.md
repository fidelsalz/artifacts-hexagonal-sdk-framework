# Character Designer — Task Instructions

Your cwd is the `A##R##` arc folder inside `INT/`.
The angle folder (`INT/A##/`) and the section folder (`INT/`) are available as extra directories.

Your inputs are:
- `A*R*.md` — narrative concept (in your cwd)
- `A*R*-execution.md` — execution style, if present (in your cwd)
- `../A*.md` — angle brief (in the extra angle dir)
- `../../research.md` — audience intelligence: pains, language, demographics (in the extra INT dir)

**Do NOT modify files in the angle or INT directories — they are read-only context.**

**Before starting:** check if `A*R*-execution.md` exists in your cwd.
- If it contains `**Has Presenter:** false` → inform the user that this arc uses a
  Product Showcase style with no on-camera presenter, so character generation is not
  needed. Ask if they want to proceed anyway or skip. Do not scaffold folders unless confirmed.
- If presenter is true or the file is absent → proceed normally.
If an execution style file is present and `Has Presenter: true`, read the
Micro-Expressions & Body Language section and use those cues to shape the character's
expression, wardrobe energy, and negative constraints in your profile proposal.

> The character you define here is shared across all hooks of this arc and across
> all ad images generated for this arc. Define it once; it propagates everywhere.

---

## Mission

Produce a single approved reference image of the main character for this ad.

**Tool constraint:** Use the `Bash` tool to run `higgsfield` CLI commands exclusively.
Do NOT use any Higgsfield MCP tools — they are not available in this agent environment.
The character must embody the target audience — they are the person the viewer
sees themselves in. Visual consistency across all shots depends on this image
being approved before scene-specs or image-prompts runs.

---

## Step 1 — Scaffold the folder tree

```bash
mkdir -p assets/character/attempts assets/character/disapproved assets/character/approved
```

---

## Step 2 — Read context and propose a character profile

Read all input files listed above. Then present a character profile to the user
in plain language covering:

- **Age range** — be specific (e.g. "late 30s to mid 40s")
- **Gender**
- **Ethnicity / skin tone**
- **Body type / physique**
- **Wardrobe** — 2–3 specific items (color, style, fabric feel)
- **Expression and energy** — what emotion do they project?
- **Hair** — length, color, style
- **Negative constraints** — what the character must NOT look like (avoid stock-photo clichés)

Do NOT generate an image yet. Ask the user: "Does this profile match your vision, or would you like to adjust anything?"

Wait for confirmation or adjustments before continuing.

---

## Step 3 — Select a model

Once the profile is confirmed, run `higgsfield model list --image` and present the available
image models clearly. Ask the user which model to use. Suggest lower-cost options first:
`nano_banana_2` (stylized/illustrated, no quality flag needed) or `gpt_image_2` at `--quality low`
(realistic, supports quality/resolution flags). Only recommend higher-fidelity settings if the
user asks.

---

## Step 4 — Build the generation prompt

Translate the confirmed profile into a single-sentence Higgsfield image prompt. The prompt must:
- Describe the character with enough specificity to reproduce them consistently
- Frontal portrait, plain neutral background — this is a reference image, not a scene. No setting, no props, no scenario.
- End with style/quality keywords (e.g. "photorealistic, natural lighting, ad-quality")

Show the prompt to the user and confirm before generating.

---

## Step 5 — Generate and iterate

**On each attempt:**

1. Count existing files in `assets/character/attempts/` to determine the attempt number:
   ```bash
   ls assets/character/attempts/ | wc -l
   ```
   Use the next number (e.g. `attempt-001.png`, `attempt-002.png`, …)

2. Before generating, run `higgsfield model get <model>` to confirm accepted params.
   Generate the image with the lowest cost settings by default:
   ```bash
   higgsfield generate create <model> \
     --prompt "<confirmed prompt>" \
     --aspect_ratio "2:3" \
     --resolution 1k \
     --quality low \
     --wait --json
   ```
   **`--quality` is model-dependent** — only pass it for models that accept it (e.g. `gpt_image_2`).
   For models that do not support it (e.g. `nano_banana_2`, `flux_2`), omit `--quality` entirely
   or the job will fail. Only upgrade resolution or quality if the user explicitly requests it.

   Capture `id` (job_id) and `result_url` from the JSON output.

3. Download the image to the attempts folder:
   ```bash
   curl -L "<result_url>" -o assets/character/attempts/attempt-NNN.png
   ```

4. Display the image:
   ```
   ![Character attempt NNN](assets/character/attempts/attempt-NNN.png)
   ```
   Tell the user the image is ready and ask: **approve or disapprove?**

**If disapproved:**
- Ask for specific feedback ("What should change? Hair color? Expression? Wardrobe?")
- Move the attempt to `disapproved/`:
  ```bash
  mv assets/character/attempts/attempt-NNN.png assets/character/disapproved/
  ```
- Refine the generation prompt based on feedback
- Show the updated prompt and confirm before generating the next attempt

**If approved:**
- Copy the approved image:
  ```bash
  cp assets/character/attempts/attempt-NNN.png assets/character/approved/approved.png
  ```
- Write `assets/character/character.json` (see schema below)
- Tell the user the character is locked and ready for scene-specs

---

## Output: `assets/character/character.json`

```json
{
  "character_id": "CHAR001",
  "description": "One sentence describing who this character is",
  "visual_identity": {
    "age": "late 30s",
    "gender": "woman",
    "ethnicity": "Latina",
    "physique": "average build, slightly overweight",
    "appearance": "warm brown skin, shoulder-length dark brown hair, minimal makeup",
    "wardrobe": "comfortable gray hoodie, dark jeans, no jewelry",
    "expression": "tired but hopeful, authentic",
    "negative_constraints": "no stock-photo smile, no fitness-model body, no professional lighting"
  },
  "generation_prompt": "Full Higgsfield prompt used for the approved image",
  "model_used": "model-id-used",
  "attempt_count": 2,
  "approved_image": "assets/character/approved/approved.png",
  "higgsfield_job_id": "job-id-of-the-approved-generation"
}
```

`higgsfield_job_id` is the `id` field returned by the CLI `--json` output for the approved
generation. Downstream agents (image-generation, generated-clips, ml-creator) pass this value
directly as `--image <higgsfield_job_id>` — Higgsfield accepts prior job IDs as media references
without re-uploading.

---

## Notes

- Check balance with `higgsfield account status` if a job fails unexpectedly.
- Never skip the user confirmation step between profile proposal and image generation.
- The generation prompt in `character.json` is the canonical reference — downstream agents
  (scene-specs, image-prompts) will embed it verbatim into their prompts to lock visual identity.

<!-- Inputs: {cwd}/A*R*.md, {extra_angle_dir}/A*.md, {extra_int_dir}/research.md -->
<!-- Output: {cwd}/assets/character/character.json, {cwd}/assets/character/approved/approved.png -->
<!-- Shared via promote-hook → SCE/A##R##H##/assets/character/ and promote-arc → IMG/ML/A##R##/assets/character/ -->
