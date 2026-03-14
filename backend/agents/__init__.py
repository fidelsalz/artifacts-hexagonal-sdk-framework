import importlib
import sys

from .base import AgentBase

# Explicit agent classes (one file per agent)
EXPLICIT: dict[str, tuple[str, str]] = {}

# Generic coding agents (use CodingAgent parameterised by id)
CODING_AGENT_IDS = {"ports", "hexagon", "adapters", "infra"}

# Validators driven by agents-config.yaml
VALIDATOR_IDS = {"ports-validator", "hexagon-validator", "adapters-validator", "infra-validator"}

# Legacy / one-off agents registered by module + class name
REGISTRY: dict[str, tuple[str, str]] = {
    "sample":   ("agents.sample",  "SampleAgent"),
    "sample-2": ("agents.agent-2", "SampleAgent"),
}


def get_agent(name: str) -> AgentBase:
    if name in EXPLICIT:
        module_name, class_name = EXPLICIT[name]
        import importlib, sys
        module = importlib.reload(sys.modules[module_name]) if module_name in sys.modules \
                 else importlib.import_module(module_name)
        return getattr(module, class_name)()

    if name in CODING_AGENT_IDS:
        from .coding_agent import CodingAgent
        return CodingAgent(name)

    if name in VALIDATOR_IDS:
        from .validator_agent import ValidatorAgent
        return ValidatorAgent(name)

    entry = REGISTRY.get(name)
    if entry is None:
        raise ValueError(f"Unknown agent: {name!r}")
    module_name, class_name = entry
    if module_name in sys.modules:
        module = importlib.reload(sys.modules[module_name])
    else:
        module = importlib.import_module(module_name)
    return getattr(module, class_name)()
