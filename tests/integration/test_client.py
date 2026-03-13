from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

import pytest
from tests.fixtures import (
    ASSISTANT_ERROR_STREAM_RESPONSE,
    ASSISTANT_HISTORY_PAYLOAD,
    ASSISTANT_HOME_SESSIONS_AFTER_PAYLOAD,
    ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    ASSISTANT_PAPER_SESSIONS_PAYLOAD,
    ASSISTANT_STREAM_RESPONSE,
    ASSISTANT_USER_PAYLOAD,
    COMMENT_CREATE_RESPONSE,
    COMMENT_REPLY_RESPONSE,
    COMMENT_UPVOTE_RESPONSE,
    COMMENTS_PAYLOAD,
    EXPLORE_FEED_PAYLOAD,
    FOLDERS_PAYLOAD,
    FULL_TEXT_PAYLOAD,
    LEGACY_PAYLOAD,
    MENTIONS_PAYLOAD,
    ORGANIZATION_SEARCH_PAYLOAD,
    OVERVIEW_PAYLOAD,
    OVERVIEW_STATUS_PAYLOAD,
    PAPER_VIEW_RESPONSE,
    PAPER_VOTE_RESPONSE,
    SEARCH_PAYLOAD,
    SIMILAR_PAPERS_PAYLOAD,
    TOPIC_SEARCH_PAYLOAD,
    TRANSCRIPT_PAYLOAD,
    URL_METADATA_PAYLOAD,
)

from alphaxiv import AlphaXivClient
from alphaxiv.auth import build_saved_api_key, save_api_key
from alphaxiv.exceptions import APIError, AuthRequiredError, ResolutionError


@pytest.mark.asyncio
async def test_search_papers(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/search/v2/paper/fast?q=helios&includePrivate=false",
        json=SEARCH_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        results = await client.search.papers("helios")

    assert len(results) == 1
    assert results[0].paper_id == "2603.04379"


@pytest.mark.asyncio
async def test_from_saved_api_key_sends_authorization_header(
    httpx_mock, monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_api_key(build_saved_api_key("axv1_saved-token"))
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/search/v2/paper/fast?q=helios&includePrivate=false",
        match_headers={"Authorization": "Bearer axv1_saved-token"},
        json=SEARCH_PAYLOAD,
    )

    async with AlphaXivClient.from_saved_api_key() as client:
        results = await client.search.papers("helios")

    assert len(results) == 1
    assert results[0].paper_id == "2603.04379"


@pytest.mark.asyncio
async def test_homepage_search_and_feed(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/search/v2/paper/fast?q=reinforcement+learning&includePrivate=false",
        json=SEARCH_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/organizations/v2/search?q=reinforcement+learning",
        json=ORGANIZATION_SEARCH_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/v1/search/closest-topic?input=reinforcement+learning",
        json=TOPIC_SEARCH_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/organizations/v2/top",
        json=ORGANIZATION_SEARCH_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            "https://api.alphaxiv.org/papers/v3/feed?pageNum=0&pageSize=20&sort=Hot"
            "&interval=All+time&organizations=%5B%22MIT%22%5D"
            "&categories=%5B%22computer-science%22%5D"
            "&subcategories=%5B%22machine-learning%22%5D&source=Twitter+%28X%29"
        ),
        json=EXPLORE_FEED_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        results = await client.search.homepage("reinforcement learning")
        filters = await client.explore.filter_options()
        cards = await client.explore.feed(
            sort="Hot",
            organizations=("MIT",),
            categories=("computer-science",),
            subcategories=("machine-learning",),
            source="Twitter (X)",
        )

    assert results.organizations[0].name == "MIT"
    assert results.topics == ["deep-reinforcement-learning", "reinforcement-learning"]
    assert filters.organizations[0].slug == "mit"
    assert len(cards) == 2
    assert cards[1].paper_id == "2512.24601"
    assert cards[1].x_likes == 325


@pytest.mark.asyncio
async def test_feed_filter_search(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/v1/search/closest-topic?input=agentic",
        json={"data": ["agentic-frameworks", "agents"]},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/organizations/v2/search?q=agentic",
        json=ORGANIZATION_SEARCH_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        results = await client.explore.search_filters("agentic")

    assert results.topics == ["agentic-frameworks", "agents"]
    assert results.organizations[0].name == "MIT"


@pytest.mark.asyncio
async def test_get_bare_id_resolution(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379",
        json=LEGACY_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        paper = await client.papers.get("2603.04379")

    assert paper.resolved.canonical_id == "2603.04379v1"
    assert paper.version.id == "019cbc05-f158-7e3a-b9c1-a43274c0130b"


@pytest.mark.asyncio
async def test_overview_and_resources(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379v1",
        json=LEGACY_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/019cbc05-f158-7e3a-b9c1-a43274c0130b/overview/en",
        json=OVERVIEW_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/x-mentions-db/019cbc05-f11c-75c7-a13b-b028107d6a76",
        json=MENTIONS_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        overview = await client.papers.overview("2603.04379v1")
        resources = await client.papers.resources("2603.04379v1")

    assert overview.summary is not None
    assert overview.summary.results == ["19.53 FPS on H100."]
    assert len(resources.mentions) == 1
    assert resources.implementations[0].url == "https://github.com/PKU-YuanGroup/Helios"
    assert resources.citation is not None
    assert "@article{yuan2026helios" in resources.citation
    assert (
        resources.podcast_url
        == "https://paper-podcasts.alphaxiv.org/019cbc05-f11c-75c7-a13b-b028107d6a76/podcast.mp3"
    )
    assert (
        resources.transcript_url
        == "https://paper-podcasts.alphaxiv.org/019cbc05-f11c-75c7-a13b-b028107d6a76/transcript.json"
    )


@pytest.mark.asyncio
async def test_paper_comments(httpx_mock) -> None:
    comments_legacy_payload = cast(dict[str, Any], deepcopy(LEGACY_PAYLOAD))
    paper_payload = cast(dict[str, Any], comments_legacy_payload["paper"])
    paper_version = cast(dict[str, Any], paper_payload["paper_version"])
    paper_group = cast(dict[str, Any], paper_payload["paper_group"])
    paper_version["id"] = "0189b531-a930-7613-9d2e-dd918c8435a5"
    paper_version["version_label"] = "v7"
    paper_version["universal_paper_id"] = "1706.03762"
    paper_version["title"] = "Attention Is All You Need"
    paper_group["id"] = "015c9ef4-ac30-768d-928b-847320902575"
    paper_group["universal_paper_id"] = "1706.03762"
    paper_group["title"] = "Attention Is All You Need"
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/1706.03762v7",
        json=comments_legacy_payload,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/015c9ef4-ac30-768d-928b-847320902575/comments",
        json=COMMENTS_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        comments = await client.papers.comments("1706.03762v7")

    assert len(comments) == 1
    assert comments[0].author is not None
    assert comments[0].author.display_name == "Research Reader"
    assert comments[0].responses[0].is_author is True


@pytest.mark.asyncio
async def test_create_comment(httpx_mock) -> None:
    comments_legacy_payload = cast(dict[str, Any], deepcopy(LEGACY_PAYLOAD))
    paper_payload = cast(dict[str, Any], comments_legacy_payload["paper"])
    paper_version = cast(dict[str, Any], paper_payload["paper_version"])
    paper_group = cast(dict[str, Any], paper_payload["paper_group"])
    paper_version["id"] = "0189b531-a930-7613-9d2e-dd918c8435a5"
    paper_version["version_label"] = "v7"
    paper_version["universal_paper_id"] = "1706.03762"
    paper_version["title"] = "Attention Is All You Need"
    paper_group["id"] = "015c9ef4-ac30-768d-928b-847320902575"
    paper_group["universal_paper_id"] = "1706.03762"
    paper_group["title"] = "Attention Is All You Need"
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/1706.03762v7",
        json=comments_legacy_payload,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/papers/v2/0189b531-a930-7613-9d2e-dd918c8435a5/comment",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        match_json={
            "body": "Helpful thread.",
            "title": "Useful note",
            "tag": "general",
            "parentCommentId": None,
        },
        json=COMMENT_CREATE_RESPONSE,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        comment = await client.papers.create_comment(
            "1706.03762v7",
            body="Helpful thread.",
            title="Useful note",
        )

    assert comment.id == "comment-root"
    assert comment.parent_comment_id is None
    assert comment.body == COMMENT_CREATE_RESPONSE["body"]


@pytest.mark.asyncio
async def test_reply_to_comment(httpx_mock) -> None:
    comments_legacy_payload = cast(dict[str, Any], deepcopy(LEGACY_PAYLOAD))
    paper_payload = cast(dict[str, Any], comments_legacy_payload["paper"])
    paper_version = cast(dict[str, Any], paper_payload["paper_version"])
    paper_group = cast(dict[str, Any], paper_payload["paper_group"])
    paper_version["id"] = "0189b531-a930-7613-9d2e-dd918c8435a5"
    paper_version["version_label"] = "v7"
    paper_version["universal_paper_id"] = "1706.03762"
    paper_version["title"] = "Attention Is All You Need"
    paper_group["id"] = "015c9ef4-ac30-768d-928b-847320902575"
    paper_group["universal_paper_id"] = "1706.03762"
    paper_group["title"] = "Attention Is All You Need"
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/1706.03762v7",
        json=comments_legacy_payload,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/papers/v2/0189b531-a930-7613-9d2e-dd918c8435a5/comment",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        match_json={
            "body": "Thanks for the answer.",
            "title": None,
            "tag": "research",
            "parentCommentId": "comment-root",
        },
        json=COMMENT_REPLY_RESPONSE,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        comment = await client.papers.reply_to_comment(
            "1706.03762v7",
            "comment-root",
            body="Thanks for the answer.",
            tag="research",
        )

    assert comment.id == "comment-child"
    assert comment.parent_comment_id == "comment-root"
    assert comment.body == COMMENT_REPLY_RESPONSE["body"]


@pytest.mark.asyncio
async def test_create_comment_rejects_invalid_tag(httpx_mock) -> None:
    async with AlphaXivClient(api_key="axv1_test-token") as client:
        with pytest.raises(ValueError):
            await client.papers.create_comment(
                "1706.03762v7",
                body="Helpful thread.",
                tag="question",
            )

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_create_comment_with_version_uuid(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/papers/v2/0189b531-a930-7613-9d2e-dd918c8435a5/comment",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        match_json={
            "body": "Helpful thread.",
            "title": None,
            "tag": "general",
            "parentCommentId": None,
        },
        json=COMMENT_CREATE_RESPONSE,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        comment = await client.papers.create_comment(
            "0189b531-a930-7613-9d2e-dd918c8435a5",
            body="Helpful thread.",
        )

    assert comment.paper_version_id == "0189b531-a930-7613-9d2e-dd918c8435a5"


@pytest.mark.asyncio
async def test_paper_similar_dedupes_results(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/2603.04379v1/similar-papers",
        json=SIMILAR_PAPERS_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        cards = await client.papers.similar("2603.04379v1")

    assert len(cards) == 2
    assert cards[0].paper_id == "2603.04379"
    assert cards[1].paper_id == "2512.24601"


@pytest.mark.asyncio
async def test_paper_similar_rejects_uuid_inputs(httpx_mock) -> None:
    async with AlphaXivClient() as client:
        with pytest.raises(ResolutionError):
            await client.papers.similar("019cbc05-f158-7e3a-b9c1-a43274c0130b")


@pytest.mark.asyncio
async def test_overview_status_and_transcript(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379v1",
        json=LEGACY_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/019cbc05-f158-7e3a-b9c1-a43274c0130b/overview/status",
        json=OVERVIEW_STATUS_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://paper-podcasts.alphaxiv.org/019cbc05-f11c-75c7-a13b-b028107d6a76/transcript.json",
        json=TRANSCRIPT_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        status = await client.papers.overview_status("2603.04379v1")
        transcript = await client.papers.transcript("2603.04379v1")
        bibtex = await client.papers.bibtex("2603.04379v1")

    assert status.state == "done"
    assert sorted(status.translations) == ["en", "fr"]
    assert len(transcript.lines) == 2
    assert transcript.lines[1].speaker == "Noah"
    assert bibtex is not None
    assert "@article{yuan2026helios" in bibtex


@pytest.mark.asyncio
async def test_full_text_by_version_uuid(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/019cbc05-f158-7e3a-b9c1-a43274c0130b/full-text",
        json=FULL_TEXT_PAYLOAD,
    )

    async with AlphaXivClient() as client:
        full_text = await client.papers.full_text("019cbc05-f158-7e3a-b9c1-a43274c0130b")

    assert full_text.resolved.version_id == "019cbc05-f158-7e3a-b9c1-a43274c0130b"
    assert full_text.page_count == 2
    assert full_text.pages[1].page_number == 2


@pytest.mark.asyncio
async def test_pdf_download(httpx_mock, tmp_path) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379v1",
        json=LEGACY_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://fetcher.alphaxiv.org/v2/pdf/2603.04379v1.pdf",
        content=b"%PDF-1.4 test pdf",
    )

    async with AlphaXivClient() as client:
        output_path = await client.papers.download_pdf("2603.04379v1", tmp_path / "helios.pdf")

    assert output_path.exists()
    assert output_path.read_bytes() == b"%PDF-1.4 test pdf"


@pytest.mark.asyncio
async def test_paper_record_view(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379v1",
        json=LEGACY_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/papers/v3/019cbc05-f11c-75c7-a13b-b028107d6a76/view",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=PAPER_VIEW_RESPONSE,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        response = await client.papers.record_view("2603.04379v1")

    assert response == PAPER_VIEW_RESPONSE


@pytest.mark.asyncio
async def test_paper_toggle_vote(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379v1",
        json=LEGACY_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/v2/papers/019cbc05-f11c-75c7-a13b-b028107d6a76/vote",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=PAPER_VOTE_RESPONSE,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        response = await client.papers.toggle_vote("2603.04379v1")

    assert response == PAPER_VOTE_RESPONSE


@pytest.mark.asyncio
async def test_folders_list(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/folders/v3",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=FOLDERS_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        folders = await client.folders.list()

    assert len(folders) == 2
    assert folders[0].papers[0].preferred_id == "2603.04379v1"


@pytest.mark.asyncio
async def test_folders_get_by_name(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/folders/v3",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=FOLDERS_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        folder = await client.folders.get("Reading List")

    assert folder.id == "folder-reading"


@pytest.mark.asyncio
async def test_folders_add_papers(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/folders/v3",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=FOLDERS_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/folders/v3/folder-reading/add-papers",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        match_json={"paperGroupIds": ["019cbc05-f11c-75c7-a13b-b028107d6a76"]},
        status_code=204,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/folders/v3",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=FOLDERS_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        folder = await client.folders.add_papers(
            "folder-reading",
            ["019cbc05-f11c-75c7-a13b-b028107d6a76"],
        )

    assert folder.id == "folder-reading"


@pytest.mark.asyncio
async def test_folders_remove_papers(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/folders/v3",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=FOLDERS_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/folders/v3/folder-reading/remove-papers",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        match_json={"paperGroupIds": ["019cbc05-f11c-75c7-a13b-b028107d6a76"]},
        status_code=204,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/folders/v3",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=FOLDERS_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        folder = await client.folders.remove_papers(
            "Reading List",
            ["019cbc05-f11c-75c7-a13b-b028107d6a76"],
        )

    assert folder.id == "folder-reading"


@pytest.mark.asyncio
async def test_comment_toggle_upvote(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/comments/v2/comment-root/upvote",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=COMMENT_UPVOTE_RESPONSE,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        response = await client.comments.toggle_upvote("comment-root")

    assert response == COMMENT_UPVOTE_RESPONSE


@pytest.mark.asyncio
async def test_comment_delete(httpx_mock) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url="https://api.alphaxiv.org/comments/v2/comment-root",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        status_code=204,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        await client.comments.delete("comment-root")


@pytest.mark.asyncio
async def test_comment_mutations_require_auth() -> None:
    async with AlphaXivClient() as client:
        with pytest.raises(AuthRequiredError):
            await client.papers.create_comment("1706.03762v7", body="Helpful thread.")
        with pytest.raises(AuthRequiredError):
            await client.papers.reply_to_comment(
                "1706.03762v7",
                "comment-root",
                body="Thanks for the answer.",
            )
        with pytest.raises(AuthRequiredError):
            await client.comments.toggle_upvote("comment-root")
        with pytest.raises(AuthRequiredError):
            await client.comments.delete("comment-root")


@pytest.mark.asyncio
async def test_assistant_boundary_raises_auth_required() -> None:
    async with AlphaXivClient() as client:
        with pytest.raises(AuthRequiredError):
            await client.assistant.ask("What is the main idea?", paper_id="2603.04379")


@pytest.mark.asyncio
async def test_assistant_list_homepage(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        sessions = await client.assistant.list()

    assert len(sessions) == 1
    assert sessions[0].id == "session-existing"
    assert sessions[0].title == "Earlier chat"


@pytest.mark.asyncio
async def test_assistant_list_for_paper(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379v1",
        json=LEGACY_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=paper&paperVersion=019cbc05-f158-7e3a-b9c1-a43274c0130b",
        json=ASSISTANT_PAPER_SESSIONS_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        sessions = await client.assistant.list(paper_id="2603.04379v1")

    assert len(sessions) == 1
    assert sessions[0].id == "paper-session"


@pytest.mark.asyncio
async def test_assistant_history(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2/session-existing/messages",
        json=ASSISTANT_HISTORY_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        history = await client.assistant.history("session-existing")

    assert len(history) == 3
    assert history[1].message_type == "output_text"
    assert history[1].content == "Helios is a real-time long video generation model."


@pytest.mark.asyncio
async def test_assistant_url_metadata(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2/url-metadata?url=https%3A%2F%2Fgithub.com%2FPKU-YuanGroup%2FHelios",
        match_headers={"Authorization": "Bearer axv1_test-token"},
        json=URL_METADATA_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        metadata = await client.assistant.url_metadata("https://github.com/PKU-YuanGroup/Helios")

    assert metadata.title == "PKU-YuanGroup/Helios"
    assert metadata.site_name == "GitHub"


@pytest.mark.asyncio
async def test_assistant_ask_new_chat(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/users/v3",
        json=ASSISTANT_USER_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/assistant/v2/chat",
        match_json={
            "message": "Tell me about Helios.",
            "files": [],
            "llmChatId": None,
            "model": "claude-4.6-sonnet",
            "thinking": True,
            "webSearch": "off",
            "parentMessageId": None,
            "paperVersionId": None,
            "selectionPageRange": None,
        },
        text=ASSISTANT_STREAM_RESPONSE,
        headers={"content-type": "text/event-stream"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_AFTER_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        run = await client.assistant.ask("Tell me about Helios.")

    assert run.session_id == "session-new"
    assert run.session_title == "Helios follow-up"
    assert run.output_text == "Helios is a real-time long video generation model."
    assert run.reasoning_text == "Searching alphaXiv..."
    assert run.error_message is None


@pytest.mark.asyncio
async def test_assistant_reply_existing_chat(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2/session-existing/messages",
        json=ASSISTANT_HISTORY_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/users/v3",
        json=ASSISTANT_USER_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/assistant/v2/chat",
        match_json={
            "message": "Summarize it in one sentence.",
            "files": [],
            "llmChatId": "session-existing",
            "model": "claude-4.6-sonnet",
            "thinking": True,
            "webSearch": "off",
            "parentMessageId": "message-output",
            "paperVersionId": None,
            "selectionPageRange": None,
        },
        text=ASSISTANT_STREAM_RESPONSE,
        headers={"content-type": "text/event-stream"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        run = await client.assistant.ask(
            "Summarize it in one sentence.",
            session_id="session-existing",
        )

    assert run.session_id == "session-existing"
    assert run.output_text == "Helios is a real-time long video generation model."


@pytest.mark.asyncio
async def test_assistant_error_event_is_aggregated(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/users/v3",
        json=ASSISTANT_USER_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/assistant/v2/chat",
        text=ASSISTANT_ERROR_STREAM_RESPONSE,
        headers={"content-type": "text/event-stream"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_AFTER_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        run = await client.assistant.ask("Force an assistant error.")

    assert run.session_id == "session-new"
    assert run.error_message == "Assistant backend failed"


@pytest.mark.asyncio
async def test_assistant_set_preferred_model(httpx_mock) -> None:
    httpx_mock.add_response(
        method="PATCH",
        url="https://api.alphaxiv.org/users/v3/preferences",
        match_json={"base": {"preferredLlmModel": "gpt-5.4"}},
        json={"ok": True},
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        model = await client.assistant.set_preferred_model("GPT 5.4")

    assert model == "gpt-5.4"


@pytest.mark.asyncio
async def test_assistant_preferred_model(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/users/v3",
        json=ASSISTANT_USER_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        model = await client.assistant.preferred_model()

    assert model == "claude-4.6-sonnet"


@pytest.mark.asyncio
async def test_assistant_preferred_model_preserves_live_provider_prefix(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/users/v3",
        json={"preferences": {"base": {"preferredLlmModel": "openai-gpt-5.4"}}},
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        model = await client.assistant.preferred_model()

    assert model == "openai-gpt-5.4"


@pytest.mark.asyncio
async def test_assistant_ask_canonicalizes_live_preferred_model(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/users/v3",
        json={"preferences": {"base": {"preferredLlmModel": "openai-gpt-5.4"}}},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/assistant/v2/chat",
        match_json={
            "message": "Tell me about Helios.",
            "files": [],
            "llmChatId": None,
            "model": "gpt-5.4",
            "thinking": True,
            "webSearch": "off",
            "parentMessageId": None,
            "paperVersionId": None,
            "selectionPageRange": None,
        },
        text=ASSISTANT_STREAM_RESPONSE,
        headers={"content-type": "text/event-stream"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_AFTER_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        run = await client.assistant.ask("Tell me about Helios.")

    assert run.model == "gpt-5.4"


@pytest.mark.asyncio
async def test_assistant_ask_explicit_unknown_model(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/assistant/v2/chat",
        match_json={
            "message": "Tell me about Helios.",
            "files": [],
            "llmChatId": None,
            "model": "my-new-model",
            "thinking": True,
            "webSearch": "off",
            "parentMessageId": None,
            "paperVersionId": None,
            "selectionPageRange": None,
        },
        text=ASSISTANT_STREAM_RESPONSE,
        headers={"content-type": "text/event-stream"},
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_AFTER_PAYLOAD,
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        run = await client.assistant.ask("Tell me about Helios.", model="My New Model")

    assert run.session_id == "session-new"
    assert run.model == "my-new-model"


@pytest.mark.asyncio
async def test_assistant_ask_schema_error_mentions_model(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/assistant/v2?variant=homepage",
        json=ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.alphaxiv.org/assistant/v2/chat",
        status_code=400,
        json={"message": "Request does not match schema."},
    )

    async with AlphaXivClient(api_key="axv1_test-token") as client:
        with pytest.raises(APIError, match="model 'broken-model'"):
            await client.assistant.ask("Tell me about Helios.", model="broken-model")
