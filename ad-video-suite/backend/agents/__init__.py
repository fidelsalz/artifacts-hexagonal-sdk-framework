from typing import Optional

from .conversation_agent import ConversationSession
from .config import get_agent_config

AGENT_IDS = {
    "research",
    "angles",
    "arcs",
    "timing",
    "hooks",
    "script",
    "scene-specs",
    "shots",
    "graphics",
}


def get_session(agent_id: str, cwd: str, campaign_slug: Optional[str] = None) -> ConversationSession:
    # Validate agent exists; raises ValueError if not found
    get_agent_config(agent_id, campaign_slug)
    return ConversationSession(agent_id, cwd, campaign_slug)
