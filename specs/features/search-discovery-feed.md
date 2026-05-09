# Search, Discovery, And Feed

## Status

Status: Implemented

Owner issue: pre-existing implementation before PET-8.

This spec records the current implemented surface; PET-8 does not change SDK or
CLI behavior.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "Search and Discovery" and "Routes
  Currently Used By This Repository".
- `GET /search/v2/paper/fast?q=...&includePrivate=false` supports public paper
  search.
- `GET /v1/search/closest-topic?input=...` supports public topic suggestions.
- `GET /organizations/v2/search?q=...` supports public organization search.
- `GET /organizations/v2/top` supports feed filter defaults.
- `GET /papers/v3/feed?...` supports homepage feed card retrieval.

## Acceptance Criteria

- Python users can search papers, organizations, and topics without
  authentication.
- Python users can retrieve homepage-style search suggestions and feed cards.
- CLI users can run grouped `search` and `feed` commands with JSON output where
  documented.
- Feed filtering preserves existing sort, source, topic, organization, and
  limit behavior.

## Validation Commands

```bash
uv run pytest tests/unit/test_cli_endpoints.py -q
uv run pytest tests/integration/test_client.py -q
uv run python scripts/check_specs.py
```

