# Paper Reads And Resources

## Status

Status: Implemented

Owner issues: PET-10 documents the original public-read implementation; PR #15
adds authenticated overview generation fallback behavior.

This spec records the current implemented paper read/resource surface, including
the authenticated overview generation path used when an overview is missing.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "Papers", "Related Non-API Asset
  Endpoints", and "Routes Currently Used By This Repository"; implementation
  evidence from `src/alphaxiv/_papers.py`, `src/alphaxiv/cli/paper.py`, and
  `tests/integration/test_client.py`.
- `GET /papers/v3/legacy/{bare_id}` resolves bare arXiv IDs and reads the main
  metadata payload.
- `GET /papers/v3/legacy/{canonical_or_versioned_id}` resolves versioned arXiv
  IDs and reads the main metadata payload.
- `GET /papers/v3/legacy/{paperGroupId}/comments` reads public nested comment
  threads after the paper group ID is resolved from the legacy payload.
- `GET /papers/v3/{paperVersionId}/full-text` reads page-level extracted full
  text.
- `GET /papers/v3/{paperVersionId}/overview/{lang}` reads overview or blog
  payloads in the requested language.
- `GET /papers/v3/{paperVersionId}/overview/status` reads overview generation
  and translation status.
- `POST /v2/papers/{arxivId}/versions/{n}/request-ai?preferredLanguage=...`
  requests authenticated AI overview generation for a resolved arXiv paper
  version. The SDK sends an empty JSON object and accepts the web UI's `409`
  "already requested" response as non-fatal in the get-or-generate flow.
- `GET /papers/v3/x-mentions-db/{paperGroupId}` reads social mentions and
  related-resource metadata.
- `GET /papers/v3/{paperId}/similar-papers` reads similar-paper cards for a
  bare or versioned arXiv ID.
- `POST /papers/v2/{paperVersionId}/comment` creates top-level comments and
  replies when authenticated.
- `POST /papers/v3/{paperGroupId}/view` records a paper view when
  authenticated.
- `POST /papers/v3/{paperGroupId}/like?liked={true|false}` sets a paper vote
  when authenticated; toggle behavior reads current user `votedPaperGroups`
  first.
- `https://pdfs.assets.alphaxiv.org/{canonical_id}.pdf` provides PDF
  downloads when the metadata payload omits an explicit PDF URL.
- `https://paper-podcasts.alphaxiv.org/{paperGroupId}/podcast.mp3` provides the
  podcast audio URL when the metadata payload contains a podcast path.
- `https://paper-podcasts.alphaxiv.org/{paperGroupId}/transcript.json` provides
  podcast transcripts when present.

## Identifier Behavior

- Bare arXiv IDs such as `2603.04379` and versioned IDs such as `2603.04379v1`
  are normalized before resolution.
- Bare and versioned arXiv IDs resolve through `/papers/v3/legacy/{id}` and
  cache aliases for the requested ID, versionless ID, canonical versioned ID,
  paper-version UUID, and paper-group UUID.
- Paper metadata, comments, mentions/resources, transcript retrieval, BibTeX,
  PDF URL resolution, PDF download, paper view recording, and paper voting
  require a legacy payload because they need canonical metadata or a
  paper-group UUID.
- Overview, overview status, and full text require a paper-version UUID. They
  accept a bare or versioned arXiv ID after resolution, and they also accept a
  paper-version UUID directly.
- Overview generation requires a bare or versioned arXiv ID at the request
  endpoint. SDK generation resolves paper-version UUID inputs and direct
  alphaXiv paper payloads back to canonical/versionless arXiv IDs before
  calling `/v2/papers/{arxivId}/versions/{n}/request-ai`.
- Bare-ID overview generation derives the version number from the legacy or
  direct paper payload. If the legacy route returns `404` but direct paper
  lookup succeeds, the SDK uses the direct payload instead of failing.
- Similar-paper reads accept bare or versioned arXiv IDs and send the normalized
  ID directly to `/papers/v3/{paperId}/similar-papers`; paper-version UUID
  inputs are rejected because the endpoint does not support them.
- Comment creation accepts bare or versioned arXiv IDs after resolution, and it
  also accepts a paper-version UUID directly because the write endpoint is
  scoped to `paperVersionId`.

## SDK And CLI Surface

- Python SDK: `client.papers.resolve`, `get`, `overview`, `overview_status`,
  `request_overview_ai`, `wait_for_overview`, `full_text`, `mentions`,
  `resources`, `comments`, `similar`, `transcript`, `bibtex`, `pdf_url`,
  `download_pdf`, `create_comment`, `reply_to_comment`, `record_view`, and
  `toggle_vote`.
- Client-level helper: `client.get_or_generate_overview(...)` first reads the
  public overview endpoint. If that endpoint itself returns `404`, it invokes
  an optional `on_missing` callback, requires authentication, requests overview
  generation, waits for completion, and then reads the overview again.
- Paper comment actions share the comment-level SDK helpers
  `client.comments.toggle_upvote` and `client.comments.delete`.
- CLI reads: `alphaxiv paper show`, `abstract`, `summary`, `overview`,
  `overview-status`, `resources`, `resources --bibtex`,
  `resources --transcript`, `text`, `comments list`, `similar`, `pdf url`, and
  `pdf download`.
- CLI paper actions: `alphaxiv paper comments add`, `comments reply`,
  `comments upvote`, `comments delete`, `paper view`, and `paper vote`.
- `alphaxiv paper overview` generates by default when the public overview read
  returns a true missing-overview `404`. Users can pass `--no-generate` or
  `--no-generate-if-missing` to preserve read-only behavior.
- CLI commands accept an explicit paper ID or the current paper context where
  the command is designed to support context.

## Overview Generation And Polling

- Generation requires API-key or saved browser-backed authentication. Without
  auth, `get_or_generate_overview` raises `AuthRequiredError` after confirming
  the overview endpoint is truly missing.
- A `404` from paper resolution is not treated as a missing overview. The
  get-or-generate path only starts generation when the failing URL is the
  `/overview/{lang}` endpoint, so unknown papers continue to surface the
  original paper-not-found error.
- Direct `wait_for_overview(...)` calls preserve a `404` from
  `/overview/status` immediately by default. The post-generation flow passes
  `allow_missing_status=True`, because the backend can briefly return `404`
  before the status record exists.
- Direct non-English waits fail fast when the base overview is terminal but the
  requested translation status was never queued. The post-generation flow passes
  `allow_missing_translation=True`, because the base overview can become ready
  before the translation status row appears.
- Terminal failure states such as `failed`, `error`, or `cancelled` are treated
  as generation failures rather than as readiness.

## Acceptance Criteria

- Python users can resolve bare or versioned arXiv identifiers before paper
  reads that require paper-version or group identifiers.
- Python users can use paper-version UUIDs directly for overview, overview
  status, full text, and comment creation.
- Python users can read paper metadata, public comments, full text, overview,
  overview status, mentions/resources, similar papers, transcript data, BibTeX,
  PDF URLs, and PDF downloads.
- Python users with authentication can request missing overview generation and
  use `get_or_generate_overview` to wait for the generated overview.
- Python users can run the existing authenticated paper actions for comment
  creation/replies, paper views, and paper votes without expanding the behavior.
- CLI users can access the same paper reads through grouped `paper` commands and
  the current paper context.
- CLI users can rely on `paper overview` to generate a missing overview by
  default when authenticated, or disable generation with `--no-generate`.
- CLI users can run the existing authenticated paper actions through grouped
  `paper` commands without exposing unimplemented comment editing behavior.
- Similar-paper output remains deduplicated before it is returned.
- Unsupported identifier shapes continue to raise `ResolutionError` rather than
  guessing an endpoint route.
- Overview generation preserves actionable errors: unknown-paper `404`s remain
  paper-resolution failures, permanent missing status errors remain `404`s
  outside the post-generation poller, and generation/translation failures raise
  `APIError` with failure state context.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest tests/integration/test_client.py tests/unit/test_cli_endpoints.py tests/unit/test_cli_context.py -q
ALPHAXIV_RUN_E2E=1 uv run pytest tests/e2e/test_cli_auth_smoke.py::test_cli_auth_paper_overview_default_smoke -q -rs
```
