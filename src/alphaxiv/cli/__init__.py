"""CLI registration helpers."""

from .assistant import assistant
from .explore import feed, register_explore_commands
from .paper import paper, register_paper_commands
from .pdf import pdf
from .session import register_session_commands

__all__ = [
    "assistant",
    "feed",
    "paper",
    "pdf",
    "register_explore_commands",
    "register_paper_commands",
    "register_session_commands",
]
