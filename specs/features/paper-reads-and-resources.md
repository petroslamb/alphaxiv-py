# Paper Reads And Resources

## Status

Status: Implemented

Owner issue: pre-existing implementation before PET-8.

This spec records the current implemented surface; PET-8 does not change SDK or
CLI behavior.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "Papers", "Related Non-API Asset
  Endpoints", and "Routes Currently Used By This Repository".
- `GET /papers/v3/legacy/{canonical_or_versioned_id}` resolves and reads paper
  metadata.
- `GET /papers/v3/legacy/{paperGroupId}/comments` reads public paper comments.
- `GET /papers/v3/{paperVersionId}/full-text` reads extracted full text.
- `GET /papers/v3/{paperVersionId}/overview/{lang}` reads overview or blog
  payloads.
- `GET /papers/v3/{paperVersionId}/overview/status` reads overview generation
  and translation status.
- `GET /papers/v3/x-mentions-db/{paperGroupId}` reads related resource metadata.
- `GET /papers/v3/{paperId}/similar-papers` reads similar-paper cards.
- `https://fetcher.alphaxiv.org/v2/pdf/{canonical_id}.pdf` provides PDF
  downloads.
- `https://paper-podcasts.alphaxiv.org/{paperGroupId}/transcript.json` provides
  podcast transcripts when present.

## Acceptance Criteria

- Python users can resolve bare or versioned arXiv identifiers before paper
  reads that require paper-version or group identifiers.
- Python users can read paper metadata, comments, full text, overview, overview
  status, mentions/resources, similar papers, transcript data, BibTeX, PDF URLs,
  and PDF downloads.
- CLI users can access the same paper reads through grouped `paper` commands and
  the current paper context.
- Similar-paper output remains deduplicated before it is returned.

## Validation Commands

```bash
uv run pytest tests/unit/test_cli_endpoints.py -q
uv run pytest tests/integration/test_client.py -q
uv run python scripts/check_specs.py
```

