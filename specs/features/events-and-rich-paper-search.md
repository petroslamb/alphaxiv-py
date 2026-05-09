# Events And Rich Paper Search

## Status

Status: Accepted

Owner issue: PET-15

This spec accepts two confirmed public read surfaces for future implementation:
public alphaXiv events and rich paper search. PET-15 is spec-only and does not
change SDK or CLI behavior.

## SDK Surface

- `AlphaXivClient.events.list()` returns public alphaXiv events as
  `list[Event]`.
- `AlphaXivClient.search.papers_rich(query)` returns rich public paper search
  results as `list[RichPaperSearchResult]`.
- Both methods are public unauthenticated read calls.
- Both methods require an initialized async client and follow the existing
  `AlphaXivClient` resource-group style.

## CLI Surface

- `alphaxiv events list [--json]` prints public alphaXiv events.
- `alphaxiv search papers <query> --rich [--json]` prints rich paper search
  results.
- Non-JSON output should render compact rich tables consistent with existing
  `search`, `paper`, and `feed` commands.
- JSON output should emit normalized dictionaries through
  `src/alphaxiv/cli/serialize.py`.

## Endpoint Evidence

- Evidence source: direct live probing against `https://api.alphaxiv.org` on
  2026-05-09 from the PET-15 worker clone.
- Existing inventory source: `docs/api-inventory.md`.
- Access: both endpoints returned `HTTP/2 200` without authentication.
- Implementation status: not used by `alphaxiv-py` before this spec.

| Method | Path | Parameters | Live result |
| --- | --- | --- | --- |
| `GET` | `/events/v1` | none observed | `200`, JSON list of event objects |
| `GET` | `/v1/search/paper` | `q=<query>` | `200`, JSON list of rich paper objects |

### Events Evidence

Live probe:

```bash
curl -sS -D /tmp/alphaxiv-events.headers \
  https://api.alphaxiv.org/events/v1 \
  -o /tmp/alphaxiv-events.json
```

Observed response:

- Status: `HTTP/2 200`
- Body shape: top-level JSON list.
- Sample body size: 275 bytes.
- Sample keys for each event: `id`, `title`, `speaker`, `organization`,
  `link`, `date`, `recording`.
- Sample event title observed: `Measuring and Improving Long-Horizon Reasoning
  Capabilities`.
- Sample event date observed: `2026-05-15T18:00:00.000Z`.

### Rich Paper Search Evidence

Live probe:

```bash
curl -sS -D /tmp/alphaxiv-rich-search.headers \
  'https://api.alphaxiv.org/v1/search/paper?q=attention' \
  -o /tmp/alphaxiv-rich-search.json
```

Observed response:

- Status: `HTTP/2 200`
- Body shape: top-level JSON list.
- Sample body size: 45,757 bytes for query `attention`.
- First result title observed: `Attention Is All You Need`.
- Sample top-level keys: `id`, `paper_group_id`, `title`, `abstract`,
  `paper_summary`, `image_url`, `universal_paper_id`, `metrics`,
  `first_publication_date`, `publication_date`, `updated_at`, `topics`,
  `github_stars`, `github_url`, `organization_info`, `author_info`, `authors`,
  `full_authors`, `canonical_id`, `version_id`.
- `paper_summary` keys observed when present: `summary`, `originalProblem`,
  `solution`, `keyInsights`, `results`.
- `metrics` keys observed: `visits_count`, `total_votes`,
  `public_total_votes`.
- `organization_info[]` objects include at least `name` and `image`.
- `author_info[]` objects may include `id`, `username`, `realName`, `avatar`,
  `institution`, `googleScholarId`, reputation fields, verification status,
  role, and optional social/profile identifiers.

## Inputs

### Events

- `client.events.list()` takes no required parameters for the accepted v1
  surface.
- `alphaxiv events list` takes no filter parameters for the accepted v1
  surface.
- Pagination is not accepted unless a future endpoint probe confirms stable
  parameters.

### Rich Paper Search

- `query` is required for `client.search.papers_rich(query)`.
- The CLI form is `alphaxiv search papers <query> --rich`.
- The query is passed to `/v1/search/paper` as `q=<query>`.
- Empty or whitespace-only queries should be rejected by the SDK before making
  an HTTP request.
- Pagination, limit, and private-search parameters are not accepted for this
  endpoint until live evidence confirms them.

## Outputs

### Event

Each event result should expose:

- `id`: event identifier.
- `title`: event title.
- `speaker`: speaker text when provided.
- `organization`: organizing group when provided.
- `link`: external event URL.
- `date`: event timestamp string as returned by alphaXiv.
- `recording`: recording URL or `None`.
- `raw`: original event object.

Unknown event fields must be preserved in `raw`.

### RichPaperSearchResult

Each rich paper result should expose:

- `id`: alphaXiv paper group identifier.
- `paper_group_id`: alphaXiv paper group identifier when present.
- `title`: paper title.
- `abstract`: paper abstract.
- `summary`: flattened `paper_summary.summary` when available.
- `paper_summary`: structured summary object or `None`.
- `image_url`: alphaXiv image path when present.
- `universal_paper_id`: unversioned arXiv identifier when present.
- `canonical_id`: versioned canonical arXiv identifier when present.
- `version_id`: alphaXiv paper version identifier when present.
- `publication_date`, `first_publication_date`, and `updated_at`: timestamp
  strings as returned by alphaXiv.
- `topics`: topic list.
- `github_url` and `github_stars`: repository metadata when present.
- `metrics`: raw metrics object.
- `organizations`: normalized organization objects from `organization_info`.
- `authors`: normalized author/profile objects from `author_info`, `authors`,
  and/or `full_authors` when present.
- `raw`: original rich search result object.

Unknown paper fields must be preserved in `raw`.

## Error Behavior

- HTTP status codes `429`, `500`, `502`, `503`, and `504` should use existing
  `ClientCore` retry behavior.
- Any final HTTP status code `>=400` raises `APIError` with the existing
  response-message extraction behavior.
- Network request failures raise `APIError` after retries are exhausted.
- Invalid JSON responses raise `APIError("Response was not valid JSON")`.
- Calling SDK methods outside `async with AlphaXivClient()` raises
  `RuntimeError("Client not initialized. Use 'async with AlphaXivClient()'.")`.
- Successful non-list payloads should parse as an empty list rather than
  raising, matching existing public search/feed resilience.
- Malformed non-dictionary list items should be skipped.
- CLI commands should surface SDK `APIError` failures through existing Click
  error handling.

## Acceptance Criteria

- Python users can list public alphaXiv events with `client.events.list()`.
- Python users can run richer public paper search with
  `client.search.papers_rich(query)`.
- CLI users can run `alphaxiv events list` and
  `alphaxiv search papers <query> --rich`.
- JSON and table output are documented before implementation.
- Event and rich paper result models preserve unknown fields in `raw`.
- The spec includes live endpoint evidence for both accepted endpoints.
- PET-15 makes no SDK or CLI implementation changes.
- Phase 3 implementation must not add behavior beyond this accepted spec
  without updating this spec first.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest
```
