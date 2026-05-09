# Paper Reads And Resources

## Status

Status: Implemented

Owner issue: PET-10 documents pre-existing implementation.

This spec records the current implemented surface; PET-10 does not change SDK or
CLI behavior.

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
- `GET /papers/v3/x-mentions-db/{paperGroupId}` reads social mentions and
  related-resource metadata.
- `GET /papers/v3/{paperId}/similar-papers` reads similar-paper cards for a
  bare or versioned arXiv ID.
- `POST /papers/v2/{paperVersionId}/comment` creates top-level comments and
  replies when authenticated.
- `POST /papers/v3/{paperGroupId}/view` records a paper view when
  authenticated.
- `POST /v2/papers/{paperId}/vote` toggles a paper vote when authenticated.
- `https://fetcher.alphaxiv.org/v2/pdf/{canonical_id}.pdf` provides PDF
  downloads from the PDF URL embedded in the metadata payload.
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
- Similar-paper reads accept bare or versioned arXiv IDs and send the normalized
  ID directly to `/papers/v3/{paperId}/similar-papers`; paper-version UUID
  inputs are rejected because the endpoint does not support them.
- Comment creation accepts bare or versioned arXiv IDs after resolution, and it
  also accepts a paper-version UUID directly because the write endpoint is
  scoped to `paperVersionId`.

## SDK And CLI Surface

- Python SDK: `client.papers.resolve`, `get`, `overview`, `overview_status`,
  `full_text`, `mentions`, `resources`, `comments`, `similar`, `transcript`,
  `bibtex`, `pdf_url`, `download_pdf`, `create_comment`, `reply_to_comment`,
  `record_view`, and `toggle_vote`.
- Paper comment actions share the comment-level SDK helpers
  `client.comments.toggle_upvote` and `client.comments.delete`.
- CLI reads: `alphaxiv paper show`, `abstract`, `summary`, `overview`,
  `overview-status`, `resources`, `resources --bibtex`,
  `resources --transcript`, `text`, `comments list`, `similar`, `pdf url`, and
  `pdf download`.
- CLI paper actions: `alphaxiv paper comments add`, `comments reply`,
  `comments upvote`, `comments delete`, `paper view`, and `paper vote`.
- CLI commands accept an explicit paper ID or the current paper context where
  the command is designed to support context.

## Acceptance Criteria

- Python users can resolve bare or versioned arXiv identifiers before paper
  reads that require paper-version or group identifiers.
- Python users can use paper-version UUIDs directly for overview, overview
  status, full text, and comment creation.
- Python users can read paper metadata, public comments, full text, overview,
  overview status, mentions/resources, similar papers, transcript data, BibTeX,
  PDF URLs, and PDF downloads.
- Python users can run the existing authenticated paper actions for comment
  creation/replies, paper views, and paper votes without expanding the behavior.
- CLI users can access the same paper reads through grouped `paper` commands and
  the current paper context.
- CLI users can run the existing authenticated paper actions through grouped
  `paper` commands without exposing unimplemented comment editing behavior.
- Similar-paper output remains deduplicated before it is returned.
- Unsupported identifier shapes continue to raise `ResolutionError` rather than
  guessing an endpoint route.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest tests/integration/test_client.py tests/unit/test_cli_endpoints.py -q
```
