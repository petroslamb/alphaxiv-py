from __future__ import annotations

from alphaxiv._identifiers import (
    extract_resolution_from_html,
    is_bare_arxiv_id,
    is_paper_version_uuid,
    is_versioned_arxiv_id,
    normalize_identifier,
)

from tests.fixtures import ABS_HTML


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


def test_extract_resolution_from_html() -> None:
    canonical_id, version_id, group_id = extract_resolution_from_html(ABS_HTML, "2603.04379")
    assert canonical_id == "2603.04379v1"
    assert version_id == "019cbc05-f158-7e3a-b9c1-a43274c0130b"
    assert group_id == "019cbc05-f11c-75c7-a13b-b028107d6a76"
