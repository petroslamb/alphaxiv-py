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

Live smoke layers:

- Public smoke: `ALPHAXIV_RUN_E2E=1 uv run pytest tests/e2e -q`
- Auth smoke: same command, plus `ALPHAXIV_API_KEY` in the environment
- Assistant write smoke: add `ALPHAXIV_RUN_ASSISTANT_WRITES=1`

## Public vs Authenticated Scope

This codebase intentionally supports only public alphaXiv endpoints in v1.
Assistant/chat endpoints require an alphaXiv API key. The SDK implements the authenticated `assistant/v2` flow directly over HTTP + SSE and no longer depends on browser automation.

All live smoke tests use a temporary `ALPHAXIV_HOME`, so they do not read from or write to the operator's real local CLI state.
