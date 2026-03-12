from __future__ import annotations

from alphaxiv.types import (
    FeedCard,
    Mention,
    OrganizationResult,
    OverviewStatus,
    Paper,
    PaperFullText,
    PaperTranscript,
    PaperOverview,
    ResolvedPaper,
    SearchResult,
)

from tests.fixtures import (
    FULL_TEXT_PAYLOAD,
    LEGACY_PAYLOAD,
    MENTIONS_PAYLOAD,
    ORGANIZATION_SEARCH_PAYLOAD,
    OVERVIEW_PAYLOAD,
    OVERVIEW_STATUS_PAYLOAD,
    SEARCH_PAYLOAD,
    TRANSCRIPT_PAYLOAD,
)


def test_search_result_from_payload() -> None:
    result = SearchResult.from_payload(SEARCH_PAYLOAD[0])
    assert result.paper_id == "2603.04379"
    assert result.link == "/abs/2603.04379"


def test_organization_result_from_payload() -> None:
    result = OrganizationResult.from_payload(ORGANIZATION_SEARCH_PAYLOAD[0])
    assert result.name == "MIT"
    assert result.slug == "mit"


def test_feed_card_from_payload() -> None:
    payload = {
        "id": "group-helios",
        "paper_group_id": "group-helios",
        "title": "Helios: Real Real-Time Long Video Generation Model",
        "abstract": "We introduce Helios.",
        "paper_summary": {"summary": "Helios summary", "results": ["19.53 FPS"]},
        "image_url": "image/2603.04379v1.png",
        "universal_paper_id": "2603.04379",
        "metrics": {
            "visits_count": {"all": 2974, "last_7_days": 2974},
            "total_votes": 39,
            "public_total_votes": 107,
            "x_likes": 0,
        },
        "publication_date": "2026-03-04T18:45:21.000Z",
        "updated_at": "2026-03-05T03:23:51.964Z",
        "topics": ["Computer Science", "generative-models"],
        "organization_info": [{"name": "MIT"}],
        "authors": ["Shenghai Yuan"],
        "github_stars": 235,
        "github_url": "https://github.com/PKU-YuanGroup/Helios",
        "canonical_id": "2603.04379v1",
        "version_id": "version-helios",
    }
    result = FeedCard.from_payload(payload)
    assert result.paper_id == "2603.04379"
    assert result.upvotes == 107
    assert result.github_stars == 235
    assert result.organizations == ["MIT"]
    assert result.result_highlights == ["19.53 FPS"]


def test_paper_from_payload() -> None:
    resolved = ResolvedPaper(
        input_id="2603.04379",
        versionless_id="2603.04379",
        canonical_id="2603.04379v1",
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        group_id="019cbc05-f11c-75c7-a13b-b028107d6a76",
    )
    paper = Paper.from_payload(resolved, LEGACY_PAYLOAD)
    assert paper.version.title == "Helios: Real Real-Time Long Video Generation Model"
    assert paper.group.resources[0].provider == "github"
    assert paper.pdf_url == "https://fetcher.alphaxiv.org/v2/pdf/2603.04379v1.pdf"
    assert paper.group.citation is not None
    assert "@article{yuan2026helios" in paper.group.citation


def test_paper_overview_from_payload() -> None:
    overview = PaperOverview.from_payload(
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        language="en",
        payload=OVERVIEW_PAYLOAD,
    )
    assert overview.summary is not None
    assert overview.summary.summary.startswith("Helios achieves real-time")
    assert overview.citations[0].title == "Self forcing"


def test_paper_full_text_from_payload() -> None:
    resolved = ResolvedPaper(
        input_id="1706.03762",
        versionless_id="1706.03762",
        canonical_id="1706.03762v7",
        version_id="0189b531-a930-7613-9d2e-dd918c8435a5",
        group_id="group-attention",
    )
    full_text = PaperFullText.from_payload(resolved, FULL_TEXT_PAYLOAD)
    assert full_text.page_count == 2
    assert full_text.pages[0].page_number == 1
    assert "Attention Is All You Need" in full_text.text


def test_overview_status_from_payload() -> None:
    status = OverviewStatus.from_payload(
        version_id="019cbc05-f158-7e3a-b9c1-a43274c0130b",
        payload=OVERVIEW_STATUS_PAYLOAD,
    )
    assert status.state == "done"
    assert sorted(status.translations) == ["en", "fr"]
    assert status.translations["fr"].state == "done"


def test_paper_transcript_from_payload() -> None:
    resolved = ResolvedPaper(
        input_id="1706.03762",
        versionless_id="1706.03762",
        canonical_id="1706.03762v7",
        version_id="0189b531-a930-7613-9d2e-dd918c8435a5",
        group_id="015c9ef4-ac30-768d-928b-847320902575",
    )
    transcript = PaperTranscript.from_payload(
        resolved=resolved,
        transcript_url="https://paper-podcasts.alphaxiv.org/015c9ef4-ac30-768d-928b-847320902575/transcript.json",
        payload=TRANSCRIPT_PAYLOAD,
    )
    assert len(transcript.lines) == 2
    assert transcript.lines[0].speaker == "John"
    assert "Welcome to Advanced Topics" in transcript.text


def test_mention_from_payload() -> None:
    mention = Mention.from_payload(MENTIONS_PAYLOAD["mentions"][0])
    assert mention.author_username == "why_lyon"
    assert mention.likes == 5
