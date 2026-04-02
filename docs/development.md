# Development

## Layout

- `src/alphaxiv`: package code
- `tests/unit`: parser, type, and CLI-context tests
- `tests/integration`: mocked HTTP client tests
- `tests/e2e`: live smoke tests for the public and authenticated CLI or SDK

## Test Commands

```bash
uv run pytest
ALPHAXIV_RUN_E2E=1 uv run pytest tests/e2e -q
```

If you need to work on browser-backed auth:

```bash
uv sync --extra browser
uv run playwright install chromium
```

Live smoke layers:

- Public smoke: `ALPHAXIV_RUN_E2E=1 uv run pytest tests/e2e -q`
- Auth smoke: same command, plus `ALPHAXIV_API_KEY` in the environment
- Assistant write smoke: add `ALPHAXIV_RUN_ASSISTANT_WRITES=1`
  The smoke helper prefers browser-backed auth copied from `~/.alphaxiv/browser-profile` when it
  is available, and otherwise falls back to `ALPHAXIV_API_KEY`.

## Public vs Authenticated Scope

This codebase intentionally targets direct HTTP access to alphaXiv's public and authenticated
endpoints.

Folders, comment mutations, paper votes, and paper views still use API-key auth.

Assistant commands use direct HTTP + SSE as well, but they can now authenticate through either:

- an alphaXiv API key
- a browser-backed session saved by `alphaxiv auth login-web`

This matters because some alphaXiv accounts can read assistant metadata with an API key but cannot
start or reply to assistant chats unless the request uses the browser-backed web session.

All live smoke tests use a temporary `ALPHAXIV_HOME`, so they do not read from or write to the operator's real local CLI state.
