"""CLI registration helpers."""

from .agent import agent
from .assistant import assistant
from .auth import auth
from .events import events
from .explore import feed, search
from .folders import folders
from .guide import guide
from .paper import paper
from .session import context
from .skill import skill

__all__ = [
    "agent",
    "assistant",
    "auth",
    "context",
    "events",
    "feed",
    "folders",
    "guide",
    "paper",
    "search",
    "skill",
]
