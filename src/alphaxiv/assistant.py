"""Authenticated assistant support for alphaXiv."""

from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from typing import Any, Literal

from ._core import BASE_API_URL, ClientCore
from ._papers import PapersAPI
from .exceptions import AlphaXivError, AuthRequiredError, ResolutionError
from .types import (
    AssistantMessage,
    AssistantRun,
    AssistantSession,
    AssistantStreamEvent,
    ResolvedPaper,
)

ASSISTANT_AUTH_REQUIRED_MESSAGE = (
    "alphaXiv assistant endpoints require a saved or explicit Authorization header. "
    "Run 'alphaxiv login' first, or pass authorization into AlphaXivClient(...)."
)

ASSISTANT_DEFAULT_MODEL = "claude-4.6-sonnet"
ASSISTANT_WEB_SEARCH_VALUES = {"off", "full"}


class AssistantAPI:
    """Authenticated assistant operations for alphaXiv."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core
        self._papers = PapersAPI(core)
        self._preferred_model: str | None = None

    async def preferred_model(self, *, refresh: bool = False) -> str:
        self._require_auth()
        if self._preferred_model and not refresh:
            return self._preferred_model
        payload = await self._core.get_json(f"{BASE_API_URL}/users/v3")
        if not isinstance(payload, dict):
            self._preferred_model = ASSISTANT_DEFAULT_MODEL
            return self._preferred_model
        preferred = self._extract_preferred_model(payload)
        self._preferred_model = self._normalize_model(preferred or ASSISTANT_DEFAULT_MODEL)
        return self._preferred_model

    async def set_preferred_model(self, model: str) -> str:
        self._require_auth()
        model_id = self._normalize_model(model)
        await self._core.request(
            "PATCH",
            f"{BASE_API_URL}/users/v3/preferences",
            json_data={"base": {"preferredLlmModel": model_id}},
        )
        self._preferred_model = model_id
        return model_id

    async def list(
        self,
        paper_id: str | None = None,
        limit: int | None = None,
    ) -> list[AssistantSession]:
        self._require_auth()
        params = await self._list_params(paper_id)
        payload = await self._core.get_json(f"{BASE_API_URL}/assistant/v2", params=params)
        if not isinstance(payload, list):
            raise AlphaXivError("Unexpected assistant sessions payload.")
        sessions = [AssistantSession.from_payload(item) for item in payload if isinstance(item, dict)]
        return sessions[:limit] if limit is not None else sessions

    async def history(self, session_id: str) -> list[AssistantMessage]:
        self._require_auth()
        payload = await self._core.get_json(f"{BASE_API_URL}/assistant/v2/{session_id}/messages")
        if not isinstance(payload, list):
            raise AlphaXivError(f"Unexpected assistant history payload for '{session_id}'.")
        return [AssistantMessage.from_payload(item) for item in payload if isinstance(item, dict)]

    async def stream(
        self,
        message: str,
        *,
        session_id: str | None = None,
        paper_id: str | None = None,
        model: str | None = None,
        thinking: bool = True,
        web_search: Literal["off", "full"] = "off",
    ) -> AsyncIterator[AssistantStreamEvent]:
        self._require_auth()
        paper = await self._resolve_paper(paper_id)
        payload = await self._chat_payload(
            message=message,
            session_id=session_id,
            paper=paper,
            model=model,
            thinking=thinking,
            web_search=web_search,
        )
        async for event in self._stream_chat(payload):
            yield event

    async def ask(
        self,
        message: str,
        *,
        session_id: str | None = None,
        paper_id: str | None = None,
        model: str | None = None,
        thinking: bool = True,
        web_search: Literal["off", "full"] = "off",
        on_event: Callable[[AssistantStreamEvent], Any] | None = None,
    ) -> AssistantRun:
        self._require_auth()
        paper = await self._resolve_paper(paper_id)
        variant = "paper" if paper else "homepage"
        before_sessions = await self.list(paper_id=paper_id) if session_id is None else []
        payload = await self._chat_payload(
            message=message,
            session_id=session_id,
            paper=paper,
            model=model,
            thinking=thinking,
            web_search=web_search,
        )
        resolved_model = str(payload["model"])

        events: list[AssistantStreamEvent] = []
        raw_events: list[dict[str, Any]] = []
        output_chunks: list[str] = []
        reasoning_chunks: list[str] = []
        error_message: str | None = None

        async for event in self._stream_chat(payload):
            events.append(event)
            raw_events.append(event.raw)
            if event.event_type == "delta_output_text" and event.delta:
                output_chunks.append(event.delta)
            elif event.event_type == "delta_output_reasoning" and event.delta:
                reasoning_chunks.append(event.delta)
            elif event.event_type == "output_text" and event.content:
                output_chunks.append(event.content)
            elif event.event_type == "output_reasoning" and event.content:
                reasoning_chunks.append(event.content)
            elif event.event_type == "error":
                error_message = event.error_message or "alphaXiv assistant returned an error."

            if on_event is not None:
                callback_result = on_event(event)
                if inspect.isawaitable(callback_result):
                    await callback_result

        resolved_session_id = session_id
        session_title = None
        newest_message_at = None
        if resolved_session_id is None:
            after_sessions = await self.list(paper_id=paper_id)
            session = self._derive_created_session(before_sessions, after_sessions)
            resolved_session_id = session.id if session else None
            session_title = session.title if session else None
            newest_message_at = session.newest_message_at if session else None
        else:
            sessions = await self.list(paper_id=paper_id) if paper_id else await self.list()
            for session in sessions:
                if session.id == resolved_session_id:
                    session_title = session.title
                    newest_message_at = session.newest_message_at
                    break

        return AssistantRun(
            session_id=resolved_session_id,
            session_title=session_title,
            newest_message_at=newest_message_at,
            variant=variant,
            paper=paper,
            message=message,
            model=resolved_model,
            thinking=thinking,
            web_search=web_search,
            output_text="".join(output_chunks).strip(),
            reasoning_text="".join(reasoning_chunks).strip(),
            error_message=error_message,
            events=events,
            raw=raw_events,
        )

    def _require_auth(self) -> None:
        if not self._core.authorization:
            raise AuthRequiredError(ASSISTANT_AUTH_REQUIRED_MESSAGE)

    async def _resolve_paper(self, paper_id: str | None) -> ResolvedPaper | None:
        if not paper_id:
            return None
        resolved = await self._papers.resolve(paper_id)
        if not resolved.version_id:
            raise ResolutionError(f"Could not determine a paper version UUID for '{paper_id}'.")
        return resolved

    async def _list_params(self, paper_id: str | None) -> dict[str, Any]:
        if not paper_id:
            return {"variant": "homepage"}
        paper = await self._resolve_paper(paper_id)
        return {"variant": "paper", "paperVersion": paper.version_id}

    async def _chat_payload(
        self,
        *,
        message: str,
        session_id: str | None,
        paper: ResolvedPaper | None,
        model: str | None,
        thinking: bool,
        web_search: str,
    ) -> dict[str, Any]:
        if web_search not in ASSISTANT_WEB_SEARCH_VALUES:
            raise AlphaXivError(
                f"Unsupported assistant webSearch value '{web_search}'. Expected one of: off, full."
            )

        parent_message_id = None
        if session_id:
            parent_message_id = await self._latest_parent_message_id(session_id)
        resolved_model = self._normalize_model(model) if model else await self.preferred_model()

        return {
            "message": message,
            "files": [],
            "llmChatId": session_id,
            "model": resolved_model,
            "thinking": thinking,
            "webSearch": web_search,
            "parentMessageId": parent_message_id,
            "paperVersionId": paper.version_id if paper else None,
            "selectionPageRange": None,
        }

    def _extract_preferred_model(self, payload: dict[str, Any]) -> str | None:
        candidates = [payload]
        user_payload = payload.get("user")
        if isinstance(user_payload, dict):
            candidates.append(user_payload)
        for candidate in candidates:
            preferences = candidate.get("preferences")
            if not isinstance(preferences, dict):
                continue
            base = preferences.get("base")
            if not isinstance(base, dict):
                continue
            model = base.get("preferredLlmModel")
            if isinstance(model, str) and model.strip():
                return model.strip()
        return None

    def _normalize_model(self, model: str) -> str:
        cleaned = " ".join(model.split()).strip()
        if not cleaned:
            raise AlphaXivError("Assistant model cannot be empty.")
        return cleaned.lower().replace(" ", "-")

    async def _latest_parent_message_id(self, session_id: str) -> str | None:
        messages = await self.history(session_id)
        output_messages = [message for message in messages if message.message_type == "output_text"]
        if output_messages:
            return max(output_messages, key=self._message_sort_key).id
        if messages:
            return max(messages, key=self._message_sort_key).id
        return None

    def _message_sort_key(self, message: AssistantMessage) -> tuple[float, str]:
        if message.selected_at is None:
            return (-1.0, message.id)
        return (message.selected_at.timestamp(), message.id)

    def _session_sort_key(self, session: AssistantSession) -> tuple[float, str]:
        if session.newest_message_at is None:
            return (-1.0, session.id)
        return (session.newest_message_at.timestamp(), session.id)

    def _derive_created_session(
        self,
        before_sessions: list[AssistantSession],
        after_sessions: list[AssistantSession],
    ) -> AssistantSession | None:
        before_map = {session.id: session for session in before_sessions}
        new_sessions = [session for session in after_sessions if session.id not in before_map]
        if new_sessions:
            return max(new_sessions, key=self._session_sort_key)

        changed_sessions: list[tuple[AssistantSession, float]] = []
        for session in after_sessions:
            previous = before_map.get(session.id)
            if previous is None:
                continue
            previous_ts = previous.newest_message_at.timestamp() if previous.newest_message_at else -1.0
            current_ts = session.newest_message_at.timestamp() if session.newest_message_at else -1.0
            if current_ts > previous_ts:
                changed_sessions.append((session, current_ts - previous_ts))
        if changed_sessions:
            return max(changed_sessions, key=lambda item: (item[1], self._session_sort_key(item[0])))[0]

        if after_sessions:
            return max(after_sessions, key=self._session_sort_key)
        return None

    async def _stream_chat(self, payload: dict[str, Any]) -> AsyncIterator[AssistantStreamEvent]:
        async with self._core.stream_request(
            "POST",
            f"{BASE_API_URL}/assistant/v2/chat",
            json_data=payload,
        ) as response:
            buffered_lines: list[str] = []
            async for line in response.aiter_lines():
                if not line:
                    event = self._parse_sse_event(buffered_lines)
                    buffered_lines.clear()
                    if event is not None:
                        yield event
                    continue
                if line.startswith(":"):
                    continue
                buffered_lines.append(line)

            if buffered_lines:
                event = self._parse_sse_event(buffered_lines)
                if event is not None:
                    yield event

    def _parse_sse_event(self, lines: list[str]) -> AssistantStreamEvent | None:
        if not lines:
            return None
        data_chunks = [line[5:].lstrip() for line in lines if line.startswith("data:")]
        if not data_chunks:
            return None
        data_text = "\n".join(data_chunks).strip()
        if not data_text or data_text == "[DONE]":
            return None
        try:
            payload = json.loads(data_text)
        except json.JSONDecodeError:
            return AssistantStreamEvent.from_payload(
                {"type": "raw", "content": data_text, "kind": None, "index": None}
            )
        if not isinstance(payload, dict):
            return AssistantStreamEvent.from_payload(
                {"type": "raw", "content": json.dumps(payload), "kind": None, "index": None}
            )
        return AssistantStreamEvent.from_payload(payload)
