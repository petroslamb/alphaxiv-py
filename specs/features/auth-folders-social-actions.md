# Auth, Folders, And Social Actions

## Status

Status: Implemented

Owner issue: pre-existing implementation before PET-8.

This spec records the current implemented surface; PET-8 does not change SDK or
CLI behavior.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "User and Preferences", "Voting and
  Social Actions", "Papers", and "Routes Currently Used By This Repository".
- `GET /users/v3` reads current user profile and preferences.
- `PATCH /users/v3/preferences` writes user preferences.
- `GET /folders/v3` reads authenticated folder and bookmark containers.
- `POST /papers/v2/{paperVersionId}/comment` creates top-level paper comments
  and replies.
- `POST /papers/v3/{paperGroupId}/view` records a paper view.
- `POST /v2/papers/{paperId}/vote` toggles a paper vote.
- `POST /comments/v2/{commentId}/upvote` toggles a comment upvote.
- `DELETE /comments/v2/{commentId}` deletes a comment.

## Auth Evidence

- `AlphaXivClient(api_key=...)` builds a bearer `Authorization` header from an
  API key, while `AlphaXivClient(authorization=...)` accepts an explicit bearer
  header for browser-backed sessions and other non-API-key tokens.
- `AlphaXivClient.from_saved_api_key()` loads the effective API key from
  `ALPHAXIV_API_KEY` or the local saved key and fails before constructing a
  client when neither exists.
- `AlphaXivClient.from_saved_browser_auth()` loads or refreshes the saved
  browser-backed bearer auth and fails before constructing a client when no
  usable browser auth exists.
- `AlphaXivClient.from_saved_auth(prefer_browser=True)` prefers saved browser
  auth and falls back to API-key auth; without `prefer_browser`, API-key auth is
  tried first.
- CLI `make_client()` uses the effective API key only. CLI
  `make_assistant_client()` prefers non-expired saved browser auth and falls
  back to API-key auth, matching the current assistant write workaround.
- `resolve_api_key()` gives `ALPHAXIV_API_KEY` precedence over the local
  `${ALPHAXIV_HOME:-~/.alphaxiv}/api-key.json` file.
- `auth set-api-key` validates the supplied key against `GET /users/v3` before
  saving `api-key.json` with owner-only permissions.
- `auth login-web` opens a persistent Playwright profile under
  `${ALPHAXIV_HOME:-~/.alphaxiv}/browser-profile`, extracts an alphaXiv web
  token from local storage or Clerk session state, validates it with
  `GET /users/v3`, and saves `${ALPHAXIV_HOME:-~/.alphaxiv}/auth.json` with
  owner-only permissions.
- Expired saved browser auth is refreshed from the persistent browser profile
  when possible; if refresh fails, assistant client construction falls back to
  API-key auth.
- `auth status` reports both API-key and browser-backed auth state, including
  source, token prefix, user metadata, and expiry where available.
- `auth clear` removes only `api-key.json`; `auth clear-web` removes only
  `auth.json` unless `--clear-browser-profile` is supplied.

## Local Context Evidence

- Paper CLI context is stored at
  `${ALPHAXIV_HOME:-~/.alphaxiv}/context.json` as a serialized `ResolvedPaper`.
- `context use paper <paper-id>` resolves the paper through the public paper
  resolver before saving the current paper context.
- `context show paper` best-effort hydrates a missing saved title by reading the
  current paper through the public paper endpoint and then rewriting the saved
  context with the title.
- Paper commands that accept optional paper ids use explicit arguments first and
  fall back to the saved paper context through `get_effective_identifier()`.
- `context show` prints or serializes both current paper context and current
  assistant context; `context show paper` and `context show assistant` target
  one local context file.
- `context clear paper` removes only `context.json`; bare `context clear`
  removes both `context.json` and `assistant-context.json`.

## Acceptance Criteria

- API-key auth can be loaded from `ALPHAXIV_API_KEY` or the local saved key.
- Browser-backed auth can be captured and reused for web-session-backed flows.
- Python users can list folders and perform the existing paper and comment
  social actions with authenticated clients.
- CLI users can inspect auth status, save or clear auth, list folders, create or
  reply to comments, upvote comments, delete comments, record views, and vote on
  papers through the existing grouped commands.
- Comment creation remains text-first and does not expose unsupported annotation
  editing behavior.
- Existing auth precedence, saved auth files, browser profile behavior, and clear
  semantics are documented.
- Existing paper context storage, paper-context fallback, context show, and
  context clear behavior are documented.
- This Phase 1 spec update does not change SDK or CLI behavior.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest tests/unit/test_auth.py tests/unit/test_cli_endpoints.py -q
uv run pytest tests/unit/test_cli_context.py -q
uv run pytest tests/integration/test_client.py -q
uv run pytest tests/unit -q
```
