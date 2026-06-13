"""SRT timing reconciliation for script.json.

Called at storyboard launch time. Scans script/ for any .srt file, matches
word-level SRT segments back to blueprint lines via sequential word anchoring,
and writes an updated script.json with real start_s/end_s per line.

If no SRT is present, script.json is written as a clean copy of the blueprint
(no source field) so downstream agents always find a valid file.
"""

import json
import re
import unicodedata
from pathlib import Path

# ── normalisation ────────────────────────────────────────────────────────────

# Map only unambiguous cardinal numbers — excludes "um/uma" (too common as articles).
_NUM_MAP = {
    "zero": "0", "dois": "2", "duas": "2",
    "tres": "3", "quatro": "4", "cinco": "5", "seis": "6", "sete": "7",
    "oito": "8", "nove": "9", "dez": "10", "onze": "11", "doze": "12",
    "treze": "13", "quatorze": "14", "quinze": "15", "dezesseis": "16",
    "dezessete": "17", "dezoito": "18", "dezenove": "19", "vinte": "20",
    "trinta": "30", "quarenta": "40", "cinquenta": "50", "sessenta": "60",
    "setenta": "70", "oitenta": "80", "noventa": "90", "cem": "100",
    "cento": "100",
}


# Collapse "20 e 4" → "24", "30 e 2" → "32", etc. after _NUM_MAP runs.
# Handles compound number words like "vinte e quatro" that TTS renders as "24"
# and VEED transcribes back as the numeral.
_COMPOUND_NUM_RE = re.compile(r'\b(20|30|40|50|60|70|80|90) e (\d)\b')


def _norm(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    clean = re.sub(r"[^a-z0-9\s]", "", ascii_text).strip()
    mapped = " ".join(_NUM_MAP.get(w, w) for w in clean.split())
    return _COMPOUND_NUM_RE.sub(lambda m: str(int(m.group(1)) + int(m.group(2))), mapped)


# ── SRT parsing ──────────────────────────────────────────────────────────────

def _ts_to_s(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.replace(",", ".").split(".")
    return round(int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000, 3)


def _parse_srt(srt_path: Path) -> list[dict]:
    tokens: list[dict] = []
    for block in re.split(r"\n\n+", srt_path.read_text(encoding="utf-8").strip()):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        try:
            start_str, end_str = lines[1].split(" --> ")
            tokens.append({
                "start_s": _ts_to_s(start_str.strip()),
                "end_s":   _ts_to_s(end_str.strip()),
                "text":    " ".join(lines[2:]).strip(),
            })
        except (ValueError, IndexError):
            continue
    return tokens


# ── word anchoring ───────────────────────────────────────────────────────────

def _find_first(tokens: list[dict], from_idx: int, word: str) -> int:
    """Return index of first token at or after from_idx containing word (exact normalised match)."""
    target = _norm(word)
    if not target:
        return -1
    for i in range(from_idx, len(tokens)):
        if target in _norm(tokens[i]["text"]).split():
            return i
    return -1


def _find_last(tokens: list[dict], from_idx: int, word: str, window: int = 8) -> int:
    """Return index of last token within window containing word (exact normalised match).

    Using the last occurrence prevents repeated words (e.g. percentage values)
    from anchoring too early. Window of 8 covers intra-line repetition without
    spilling into later lines (window=15 caused common words like "você" to match
    tokens belonging to the next script line).
    """
    target = _norm(word)
    if not target:
        return -1
    last = -1
    for i in range(from_idx, min(from_idx + window, len(tokens))):
        if target in _norm(tokens[i]["text"]).split():
            last = i
    return last


# ── reconciliation ───────────────────────────────────────────────────────────

def reconcile_script_timing(cwd: str | Path) -> dict:
    """Reconcile script-blueprint.json timing with a real SRT in script/.

    Returns a report dict consumed by the WS handler.
    Writes script/script.json unconditionally (SRT or blueprint fallback).
    """
    cwd = Path(cwd)
    script_dir = cwd / "script"
    blueprint_path = script_dir / "script-blueprint.json"

    if not blueprint_path.exists():
        return {
            "status": "no_blueprint",
            "message": (
                "script-blueprint.json not found in script/ — "
                "run the script agent first."
            ),
        }

    blueprint: list[dict] = json.loads(blueprint_path.read_text(encoding="utf-8"))
    srt_files = sorted(script_dir.glob("*.srt"))

    # ── no SRT: copy blueprint as script.json (strip any stale source field) ──
    if not srt_files:
        clean = [{k: v for k, v in ln.items() if k != "source"} for ln in blueprint]
        (script_dir / "script.json").write_text(
            json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return {
            "status": "no_srt",
            "message": (
                "No SRT file found in script/ — using blueprint timing estimates.\n"
                "Drop an .srt file in script/ and reopen this agent to use real audio timing."
            ),
        }

    srt_path = srt_files[0]
    tokens = _parse_srt(srt_path)
    if not tokens:
        return {
            "status": "parse_error",
            "message": f"Could not parse {srt_path.name} — check the file format.",
        }

    total_duration_s = tokens[-1]["end_s"]
    blueprint_duration_s = blueprint[-1]["end_s"] if blueprint else 0.0

    updated_lines: list[dict] = []
    line_diffs: list[dict] = []
    cursor = 0
    matched = 0

    for ln in blueprint:
        orig_start = ln["start_s"]
        orig_end   = ln["end_s"]
        words      = _norm(ln["text"]).split()

        # Anchor on first word — try first three words in case TTS skips/alters the first
        first_idx = -1
        for w in words[:3]:
            idx = _find_first(tokens, cursor, w)
            if idx != -1:
                first_idx = idx
                break

        # Anchor on last word — use last occurrence within window to handle repeated values
        last_idx = -1
        if first_idx != -1:
            for w in reversed(words[-3:]):
                idx = _find_last(tokens, first_idx, w)
                if idx != -1:
                    last_idx = idx
                    break

        if first_idx != -1 and last_idx != -1:
            new_start = tokens[first_idx]["start_s"]
            new_end   = tokens[last_idx]["end_s"]
            cursor    = last_idx + 1
            source    = "srt"
            matched  += 1
        else:
            new_start = orig_start
            new_end   = orig_end
            source    = "blueprint"

        line_diffs.append({
            "line_number": ln["line_number"],
            "orig_start":  orig_start,
            "orig_end":    orig_end,
            "new_start":   new_start,
            "new_end":     new_end,
            "source":      source,
        })
        updated_lines.append({**ln, "start_s": new_start, "end_s": new_end, "source": source})

    (script_dir / "script.json").write_text(
        json.dumps(updated_lines, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "status": "ok",
        "srt_file":            srt_path.name,
        "total_duration_s":    round(total_duration_s, 3),
        "blueprint_duration_s": round(blueprint_duration_s, 3),
        "matched":             matched,
        "total":               len(blueprint),
        "line_diffs":          line_diffs,
    }


# ── report formatting ────────────────────────────────────────────────────────

def format_timing_report(report: dict) -> str:
    status = report.get("status")

    if status in ("no_blueprint", "parse_error"):
        return f"⚠ Audio timing: {report['message']}"

    if status == "no_srt":
        return report["message"]

    # status == "ok"
    dur_real = report["total_duration_s"]
    dur_plan = report["blueprint_duration_s"]
    delta    = round(dur_real - dur_plan, 1)
    sign     = "+" if delta >= 0 else ""
    matched  = report["matched"]
    total    = report["total"]

    lines = [
        f"Audio timing loaded from {report['srt_file']}",
        f"Total audio duration: {dur_real} s  "
        f"(blueprint: {dur_plan} s — {sign}{delta} s)",
        f"Lines matched from SRT: {matched}/{total}",
        "",
    ]
    for d in report["line_diffs"]:
        n         = d["line_number"]
        o_start   = d["orig_start"]
        o_end     = d["orig_end"]
        n_start   = d["new_start"]
        n_end     = d["new_end"]
        src       = d["source"]
        end_delta = round(n_end - o_end, 1)
        sign_d    = "+" if end_delta >= 0 else ""
        flag      = " [blueprint fallback]" if src == "blueprint" else ""
        lines.append(
            f"  Line {n:2d}: {o_start}→{o_end} s  ⟹  {n_start}→{n_end} s  "
            f"({sign_d}{end_delta} s){flag}"
        )

    lines += ["", "script.json updated. Storyboard will use real audio timing."]
    return "\n".join(lines)
