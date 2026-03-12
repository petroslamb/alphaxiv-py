"""CLI registration helpers."""

from .assistant import assistant
from .auth import auth
from .explore import feed, search
from .folders import folders
from .paper import paper
from .session import context

__all__ = [
    "assistant",
    "auth",
    "context",
    "feed",
    "folders",
    "paper",
    "search",
]
