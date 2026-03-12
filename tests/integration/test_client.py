from __future__ import annotations

import pytest

from alphaxiv import AlphaXivClient
from alphaxiv.auth import build_saved_auth, save_auth
from alphaxiv.exceptions import AuthRequiredError

from tests.fixtures import (
    ABS_HTML,
    ASSISTANT_ERROR_STREAM_RESPONSE,
    ASSISTANT_HISTORY_PAYLOAD,
    ASSISTANT_HOME_SESSIONS_AFTER_PAYLOAD,
    ASSISTANT_HOME_SESSIONS_BEFORE_PAYLOAD,
    ASSISTANT_PAPER_SESSIONS_PAYLOAD,
    ASSISTANT_STREAM_RESPONSE,
    ASSISTANT_USER_PAYLOAD,
    EXPLORE_FEED_HTML,
    FULL_TEXT_PAYLOAD,
    LEGACY_PAYLOAD,
    MENTIONS_PAYLOAD,
    ORGANIZATION_SEARCH_PAYLOAD,
    OVERVIEW_PAYLOAD,
    OVERVIEW_STATUS_PAYLOAD,
    SEARCH_PAYLOAD,
    TOPIC_SEARCH_PAYLOAD,
    TRANSCRIPT_PAYLOAD,
)


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
async def test_from_saved_auth_sends_authorization_header(httpx_mock, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ALPHAXIV_HOME", str(tmp_path / ".alphaxiv"))
    save_auth(build_saved_auth("saved-token"))
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/search/v2/paper/fast?q=helios&includePrivate=false",
        match_headers={"Authorization": "Bearer saved-token"},
        json=SEARCH_PAYLOAD,
    )

    async with AlphaXivClient.from_saved_auth() as client:
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
        url="https://www.alphaxiv.org?sort=Hot&organizations=%5B%22MIT%22%5D&source=Twitter+%28X%29",
        text=EXPLORE_FEED_HTML,
    )

    async with AlphaXivClient() as client:
        results = await client.search.homepage("reinforcement learning")
        filters = await client.explore.filter_options()
        cards = await client.explore.feed(
            sort="Hot",
            organizations=("MIT",),
            categories=("machine-learning",),
            source="Twitter (X)",
        )

    assert results.organizations[0].name == "MIT"
    assert results.topics == ["deep-reinforcement-learning", "reinforcement-learning"]
    assert filters.organizations[0].slug == "mit"
    assert len(cards) == 1
    assert cards[0].paper_id == "2512.24601"
    assert cards[0].x_likes == 325


@pytest.mark.asyncio
async def test_get_bare_id_resolution(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://www.alphaxiv.org/abs/2603.04379",
        text=ABS_HTML,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/papers/v3/legacy/2603.04379v1",
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
    assert resources.podcast_url == "https://paper-podcasts.alphaxiv.org/019cbc05-f11c-75c7-a13b-b028107d6a76/podcast.mp3"
    assert resources.transcript_url == "https://paper-podcasts.alphaxiv.org/019cbc05-f11c-75c7-a13b-b028107d6a76/transcript.json"


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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
        history = await client.assistant.history("session-existing")

    assert len(history) == 3
    assert history[1].message_type == "output_text"
    assert history[1].content == "Helios is a real-time long video generation model."


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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
        model = await client.assistant.set_preferred_model("GPT 5.4")

    assert model == "gpt-5.4"


@pytest.mark.asyncio
async def test_assistant_preferred_model(httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://api.alphaxiv.org/users/v3",
        json=ASSISTANT_USER_PAYLOAD,
    )

    async with AlphaXivClient(authorization="Bearer test-token") as client:
        model = await client.assistant.preferred_model()

    assert model == "claude-4.6-sonnet"


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

    async with AlphaXivClient(authorization="Bearer test-token") as client:
        run = await client.assistant.ask("Tell me about Helios.", model="My New Model")

    assert run.session_id == "session-new"
    assert run.model == "my-new-model"
