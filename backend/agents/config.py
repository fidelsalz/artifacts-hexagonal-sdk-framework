"""YAML configuration loader for the agent team.

Resolves {{ variable }} path placeholders in order so that derived paths
(code_base, case_dir) can reference base_path without repeating it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional  # still used in dataclass fields

import yaml

CONFIG_PATH = Path(__file__).parent / "agents-config.yaml"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InSource:
    source: str
    files: list[str]


@dataclass
class ValidatorConfig:
    id: str
    name: str
    role: str
    cwd: str
    prompt_file: str
    basic_prompt: str
    model: str
    permission_mode: str
    allowed_tools: list[str]


@dataclass
class AgentConfig:
    id: str
    name: str
    role: str
    comm_type: str          # 'sse' | 'ws'
    cwd: str
    work_dir: str
    prompt_file: str
    basic_prompt: str
    model: str
    permission_mode: str
    allowed_tools: list[str]
    coding_dir: Optional[str] = None
    validator: Optional[ValidatorConfig] = None
    in_sources: list[InSource] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _resolve(value: object, vars: dict[str, str]) -> object:
    """Recursively replace {{ key }} placeholders in all strings."""
    if isinstance(value, str):
        for k, v in vars.items():
            value = value.replace(f"{{{{ {k} }}}}", v)
        return value
    if isinstance(value, dict):
        return {k: _resolve(v, vars) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(item, vars) for item in value]
    return value


def _build_vars(raw: dict) -> dict[str, str]:
    """Resolve config-section vars in declaration order so derived paths work."""
    vars: dict[str, str] = {}
    for key, val in raw.get("config", {}).items():
        resolved = str(val)
        for k, v in vars.items():
            resolved = resolved.replace(f"{{{{ {k} }}}}", v)
        vars[key] = resolved
    return vars


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_validator(raw: dict, vars: dict[str, str]) -> ValidatorConfig:
    d = _resolve(raw, vars)
    # second pass: allow {{ cwd }}, {{ prompt_file }} in basic_prompt
    validator_vars = {
        **vars,
        "cwd":         d.get("cwd", ""),
        "prompt_file": d.get("prompt_file", ""),
    }
    d["basic_prompt"] = _resolve(d["basic_prompt"], validator_vars)
    return ValidatorConfig(
        id=d["id"],
        name=d["name"],
        role=d["role"],
        cwd=d["cwd"],
        prompt_file=d["prompt_file"],
        basic_prompt=d["basic_prompt"],
        model=d["model"],
        permission_mode=d["permission_mode"],
        allowed_tools=list(d["allowed_tools"]),
    )


def _parse_agent(raw: dict, vars: dict[str, str]) -> AgentConfig:
    d = _resolve(raw, vars)
    # second pass: allow {{ cwd }}, {{ coding_dir }}, {{ work_dir }}, {{ prompt_file }} in basic_prompt
    agent_vars = {
        **vars,
        "cwd":         d.get("cwd", ""),
        "coding_dir":  d.get("coding_dir", ""),
        "work_dir":    d.get("work_dir", ""),
        "prompt_file": d.get("prompt_file", ""),
    }
    d["basic_prompt"] = _resolve(d["basic_prompt"], agent_vars)
    validator = None
    if "validator" in raw:
        validator = _parse_validator(raw["validator"], vars)
    in_sources = [
        InSource(source=s["source"], files=list(s["files"]))
        for s in d.get("in_sources", [])
    ]
    return AgentConfig(
        id=d["id"],
        name=d["name"],
        role=d["role"],
        comm_type=str(d["comm_type"]),
        cwd=d["cwd"],
        work_dir=d["work_dir"],
        prompt_file=d["prompt_file"],
        basic_prompt=d["basic_prompt"],
        model=d["model"],
        permission_mode=d["permission_mode"],
        allowed_tools=list(d["allowed_tools"]),
        coding_dir=d.get("coding_dir"),
        validator=validator,
        in_sources=in_sources,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config() -> dict[str, AgentConfig]:
    """Load agent configs from YAML on every call (no cache — reflects live edits)."""
    raw = yaml.safe_load(CONFIG_PATH.read_text())
    vars = _build_vars(raw)
    return {
        cfg_data["id"]: _parse_agent(cfg_data, vars)
        for cfg_data in raw["team"]["agents"].values()
    }


def get_agent_config(agent_id: str) -> AgentConfig:
    """Return config for a coding agent (e.g. 'ports', 'hexagon')."""
    cfg = load_config().get(agent_id)
    if cfg is None:
        raise ValueError(f"No agent config found for {agent_id!r}")
    return cfg


def get_validator_config(validator_id: str) -> tuple[AgentConfig, ValidatorConfig]:
    """Return (parent_config, validator_config) for a validator id."""
    for cfg in load_config().values():
        if cfg.validator and cfg.validator.id == validator_id:
            return cfg, cfg.validator
    raise ValueError(f"No validator config found for {validator_id!r}")
