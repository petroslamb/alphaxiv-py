from __future__ import annotations

from alphaxiv._identifiers import (
    is_bare_arxiv_id,
    is_paper_version_uuid,
    is_versioned_arxiv_id,
    normalize_identifier,
)


def test_normalize_identifier_supports_alphaxiv_urls() -> None:
    assert normalize_identifier("https://www.alphaxiv.org/abs/2603.04379") == "2603.04379"
    assert normalize_identifier("https://www.alphaxiv.org/overview/2603.04379") == "2603.04379"
    assert normalize_identifier("https://www.alphaxiv.org/resources/2603.04379") == "2603.04379"
    assert (
        normalize_identifier("https://www.alphaxiv.org/overview/2603.04379?cid=abc123")
        == "2603.04379"
    )


def test_identifier_classifiers() -> None:
    assert is_bare_arxiv_id("2603.04379")
    assert is_versioned_arxiv_id("2603.04379v1")
    assert is_paper_version_uuid("019cbc05-f158-7e3a-b9c1-a43274c0130b")
