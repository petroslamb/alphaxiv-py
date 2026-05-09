# Authenticated Assistant

## Status

Status: Implemented

Owner issue: pre-existing implementation before PET-8.

This spec records the current implemented surface; PET-8 does not change SDK or
CLI behavior.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "Assistant", "User and
  Preferences", and "Routes Currently Used By This Repository".
- `GET /assistant/v2?variant=homepage` lists homepage assistant sessions.
- `GET /assistant/v2?variant=paper&paperVersion={paperVersionId}` lists
  paper-scoped assistant sessions.
- `GET /assistant/v2/{sessionId}/messages` reads structured assistant history.
- `POST /assistant/v2/chat` starts or continues an authenticated assistant chat
  and returns SSE output.
- `GET /assistant/v2/url-metadata?url=...` reads link metadata.
- `GET /users/v3` reads the current preferred assistant model.
- `PATCH /users/v3/preferences` updates the preferred assistant model.

## Implementation Evidence

- `AlphaXivClient.assistant` exposes the existing assistant surface through
  `src/alphaxiv/assistant.py`.
- `AssistantAPI.list()` calls `/assistant/v2` with `variant=homepage` when no
  paper is provided, or resolves the paper first and calls with
  `variant=paper&paperVersion={paperVersionId}` for paper-scoped sessions.
- `AssistantAPI.history()` maps `/assistant/v2/{sessionId}/messages` payloads to
  `AssistantMessage`, preserving message type, parent message id, selected
  timestamp, tool metadata, model, feedback metadata, content, and raw payload.
- `AssistantAPI.ask()` and `AssistantAPI.stream()` post to
  `/assistant/v2/chat` with the existing payload shape: `message`, empty
  `files`, optional `llmChatId`, normalized `model`, `thinking`, `webSearch`,
  resolved `parentMessageId`, optional `paperVersionId`, and
  `selectionPageRange: null`.
- Continuing a chat derives `parentMessageId` from the latest output message in
  `history(session_id)`, falling back to the latest message when no output text
  exists.
- SSE chat responses are parsed from `data:` lines into `AssistantStreamEvent`
  records. Non-JSON data is preserved as a `raw` event, and `[DONE]` is ignored.
- `AssistantAPI.preferred_model()` reads `preferences.base.preferredLlmModel`
  from `/users/v3` and falls back to the local default `claude-4.6-sonnet` when
  the field is absent.
- `AssistantAPI.set_preferred_model()` normalizes labels such as
  `Claude 4.6 Sonnet` before writing `base.preferredLlmModel` through
  `/users/v3/preferences`.
- `AssistantAPI.url_metadata()` maps `/assistant/v2/url-metadata` payloads to
  `UrlMetadata`, including title, description, site name, author, image, favicon,
  URL, and raw payload.
- The CLI commands in `src/alphaxiv/cli/assistant.py` expose the implemented
  surface as `assistant list`, `assistant history`, `assistant model`,
  `assistant set-model`, `assistant url-metadata`, `assistant start`, and
  `assistant reply`.

## Local Context Evidence

- Assistant CLI context is persisted through `AssistantContext` in
  `${ALPHAXIV_HOME:-~/.alphaxiv}/assistant-context.json`.
- `assistant start` saves the derived session id, variant, paper association,
  title, and newest-message timestamp when a chat returns a session id.
- `assistant reply` uses an explicit leading session id when supplied, otherwise
  it falls back to the saved assistant context.
- When the saved assistant context is paper-scoped, `assistant reply` carries the
  saved paper id back into the assistant call so replies stay associated with the
  paper session.
- `assistant history` also accepts an explicit session id, otherwise it reads the
  saved assistant context.
- `context use assistant <session-id>` resolves and saves an assistant context by
  checking homepage sessions, then sessions for the current paper context, then
  history metadata for a best-effort fallback.
- `context show`, `context show assistant`, and their `--json` forms render the
  saved assistant context without contacting assistant chat endpoints.
- `context clear assistant` removes only `assistant-context.json`; bare
  `context clear` removes both paper and assistant context files.

## Acceptance Criteria

- Assistant methods require authentication and raise the existing auth error
  behavior without saved credentials.
- Browser-backed auth remains available for assistant chat writes when API-key
  chat writes are restricted.
- Python users can list sessions, read history, fetch URL metadata, read or set
  the preferred model, and start or continue homepage and paper-scoped chats.
- CLI users can access assistant list, history, model, URL metadata, start, and
  reply commands without changing command names in PET-8.
- The client does not claim a trusted live model catalog.
- Existing local assistant context behavior is documented, including the storage
  path, automatic context save after chat start, reply/history fallback to saved
  context, and paper-scoped reply carry-forward.
- This Phase 1 spec update does not change SDK or CLI behavior.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest tests/unit/test_assistant.py -q
uv run pytest tests/unit/test_auth.py -q
uv run pytest tests/unit/test_cli_context.py -q
uv run pytest tests/unit -q
```
