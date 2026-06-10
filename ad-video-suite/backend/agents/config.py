"""Configuration loader for the ad-video agent team.

Per-campaign design:
  - backend/agents/agents-config.template.yaml  — source of truth, versioned with the app
  - {campaign_dir}/agents/agents-config.yaml    — generated at campaign creation, safe to edit

At runtime, load_config() reads the active campaign's own YAML. The per-campaign YAML has all
paths fully resolved (no placeholders), so _parse_agent() is a straight read.

Global state lives in backend/settings.json:
  { "base_path": "...", "active_campaign": "..." }
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

TEMPLATE_PATH = Path(__file__).parent / "agents-config.template.yaml"
SETTINGS_PATH = Path(__file__).parent.parent / "settings.json"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentConfig:
    id: str
    name: str
    role: str
    comm_type: str
    cwd_pattern: str
    prompt_file: str
    basic_prompt: str
    model: str
    permission_mode: str
    allowed_tools: list[str]
    max_concurrent: int = 1
    sections: list[str] = field(default_factory=list)
    add_dirs: list[str] = field(default_factory=list)
    required_inputs: list[dict] = field(default_factory=list)
    output_check: str = ""


def agent_status(agent: "AgentConfig", cwd: str) -> tuple[str, list[dict]]:
    """Return (status, missing) where status is 'completed' | 'ready' | 'blocked'.

    missing is a list of required_inputs entries that are absent from cwd.
    """
    cwd_path = Path(cwd)
    if agent.output_check and list(cwd_path.glob(agent.output_check)):
        return "completed", []
    missing = [
        inp for inp in agent.required_inputs
        if not list(cwd_path.glob(inp.get("path", "")))
    ]
    return ("blocked", missing) if missing else ("ready", [])


# ---------------------------------------------------------------------------
# Settings management
# ---------------------------------------------------------------------------

def get_settings() -> dict:
    if SETTINGS_PATH.exists():
        s = json.loads(SETTINGS_PATH.read_text())
    else:
        s = {"base_path": "", "active_campaign": "", "max_active_campaigns": 3}
    if not s.get("base_path"):
        s["base_path"] = os.environ.get("BASE_PATH", "")
    return s


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))


def get_base_path() -> str:
    return get_settings().get("base_path", "")


# ---------------------------------------------------------------------------
# Path resolution (used during template generation only)
# ---------------------------------------------------------------------------

def _resolve(value: object, vars: dict[str, str]) -> object:
    """Recursively replace {key} placeholders. Safe to call with empty vars."""
    if isinstance(value, str):
        for k, v in vars.items():
            value = value.replace(f"{{{k}}}", v)
        return value
    if isinstance(value, dict):
        return {k: _resolve(v, vars) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(item, vars) for item in value]
    return value


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_agent(raw: dict, vars: dict[str, str] | None = None) -> AgentConfig:
    d = _resolve(raw, vars or {})
    return AgentConfig(
        id=d["id"],
        name=d["name"],
        role=d["role"],
        comm_type=str(d["comm_type"]),
        cwd_pattern=d["cwd_pattern"],
        prompt_file=d["prompt_file"],
        basic_prompt=d["basic_prompt"],
        model=d["model"],
        permission_mode=d["permission_mode"],
        allowed_tools=list(d["allowed_tools"]),
        max_concurrent=int(d.get("max_concurrent", 1)),
        sections=list(d.get("sections") or []),
        add_dirs=list(d.get("add_dirs") or []),
        required_inputs=list(d.get("required_inputs") or []),
        output_check=str(d.get("output_check") or ""),
    )


# ---------------------------------------------------------------------------
# Public API — config loading
# ---------------------------------------------------------------------------

def load_config(campaign_slug: Optional[str] = None) -> dict[str, AgentConfig]:
    """Load agent configs from a campaign's agents/agents-config.yaml."""
    settings = get_settings()
    slug = campaign_slug or settings.get("active_campaign", "")
    base_path = settings.get("base_path", "")
    campaign_yaml = Path(base_path) / slug / "agents" / "agents-config.yaml"
    raw = yaml.safe_load(campaign_yaml.read_text())
    return {
        cfg_data["id"]: _parse_agent(cfg_data)
        for cfg_data in raw["team"]["agents"].values()
    }


def get_agent_config(agent_id: str, campaign_slug: Optional[str] = None) -> AgentConfig:
    cfg = load_config(campaign_slug).get(agent_id)
    if cfg is None:
        raise ValueError(f"No agent config found for {agent_id!r}")
    return cfg


def load_template_config() -> dict[str, AgentConfig]:
    """Load agent configs from the app-level template (no campaign context)."""
    raw = yaml.safe_load(TEMPLATE_PATH.read_text())
    return {
        key: _parse_agent(agent_data)
        for key, agent_data in raw["team"]["agents"].items()
    }


# ---------------------------------------------------------------------------
# Campaign config generation
# ---------------------------------------------------------------------------

class _SafeRegexDumper(yaml.Dumper):
    """Dumper that single-quotes strings containing YAML flow indicators ([, {)
    so regex patterns like [A-Z]{3}$ are not mis-parsed as sequences/mappings."""


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    style = "'" if any(c in data for c in "[]{}") else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_SafeRegexDumper.add_representer(str, _str_representer)


def load_mcp_override(agent_id: str, campaign_slug: Optional[str] = None) -> dict:
    """Return the mcp_overrides entry for an agent, or {} if none configured.

    Reads the campaign's agents-config.yaml but does NOT touch AgentConfig.
    Only agents listed under the top-level mcp_overrides key are affected.
    """
    settings = get_settings()
    slug = campaign_slug or settings.get("active_campaign", "")
    base_path = settings.get("base_path", "")
    campaign_yaml = Path(base_path) / slug / "agents" / "agents-config.yaml"
    try:
        raw = yaml.safe_load(campaign_yaml.read_text())
        return (raw.get("mcp_overrides") or {}).get(agent_id) or {}
    except Exception:
        return {}


def resolve_campaign_config(slug: str, base_path: str) -> str:
    """Generate a fully-resolved agents-config.yaml string for a new campaign.

    Reads the template, replaces {campaign_dir} with the actual path, and
    returns a clean YAML string — human-readable and editable.
    """
    campaign_dir = str(Path(base_path) / slug)
    template = yaml.safe_load(TEMPLATE_PATH.read_text())

    agents_raw = template["team"]["agents"]
    resolved_agents = {}
    for key, agent_data in agents_raw.items():
        resolved = _resolve(agent_data, {"campaign_dir": campaign_dir})
        resolved_agents[key] = resolved

    output_data = {
        "team": {
            "name":        template["team"]["name"],
            "description": template["team"]["description"],
            "agents":      resolved_agents,
        },
        "mcp_overrides": template.get("mcp_overrides") or {},
    }

    header = (
        f"# agents-config.yaml — campaign: {slug}\n"
        f"# Generated from template. {campaign_dir} paths are absolute. Safe to edit.\n\n"
    )
    return header + yaml.dump(
        output_data,
        Dumper=_SafeRegexDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )


# ---------------------------------------------------------------------------
# Agent-to-folder matching
# ---------------------------------------------------------------------------

def agents_for_folder(
    folder_name: str,
    campaign_slug: Optional[str] = None,
    section: Optional[str] = None,
) -> list[AgentConfig]:
    """Return agents whose cwd_pattern matches folder_name, filtered by section if given.

    An agent is included when:
      - its cwd_pattern matches folder_name, AND
      - it declares no sections (unrestricted), OR the given section is in its sections list.
    """
    try:
        configs = load_config(campaign_slug).values()
    except Exception:
        configs = load_template_config().values()

    result = []
    for cfg in configs:
        if not re.search(cfg.cwd_pattern, folder_name):
            continue
        if cfg.sections and section not in cfg.sections:
            continue
        result.append(cfg)
    return result
