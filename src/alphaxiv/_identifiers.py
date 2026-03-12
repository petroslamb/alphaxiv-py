"""Identifier parsing and HTML resolution helpers."""

from __future__ import annotations

import re

BARE_ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}$")
VERSIONED_ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}v\d+$")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-7[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def normalize_identifier(identifier: str) -> str:
    """Normalize supported alphaXiv/arXiv identifier inputs."""
    value = identifier.strip()
    for marker in ("/abs/", "/overview/", "/resources/"):
        if marker in value:
            value = value.rstrip("/").split(marker, 1)[1]
            break
    for separator in ("?", "#"):
        if separator in value:
            value = value.split(separator, 1)[0]
    value = value.rstrip("/")
    return value


def is_bare_arxiv_id(identifier: str) -> bool:
    return bool(BARE_ARXIV_RE.fullmatch(identifier))


def is_versioned_arxiv_id(identifier: str) -> bool:
    return bool(VERSIONED_ARXIV_RE.fullmatch(identifier))


def is_paper_version_uuid(identifier: str) -> bool:
    return bool(UUID_RE.fullmatch(identifier))
