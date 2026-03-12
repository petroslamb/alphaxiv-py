# Development

## Layout

- `src/alphaxiv`: package code
- `tests/unit`: parser, type, and CLI-context tests
- `tests/integration`: mocked HTTP client tests
- `tests/e2e`: live public smoke tests

## Test Commands

```bash
uv run pytest
uv run pytest tests/e2e -m e2e
```

Set `ALPHAXIV_RUN_E2E=1` to enable live E2E tests.

## Public vs Authenticated Scope

This codebase intentionally supports only public alphaXiv endpoints in v1.
Assistant/chat endpoints require an `Authorization` header. The SDK implements the authenticated `assistant/v2` flow directly over HTTP + SSE. Playwright is optional and only used for explicit browser login; normal API-key usage does not depend on browser automation.
