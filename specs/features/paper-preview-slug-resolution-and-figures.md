# Paper Preview, Slug Resolution, And Figures

## Status

Status: Implemented

Owner issue: PET-13.

Implemented by PET-16 for the paper-side public read expansion.

## Endpoint Evidence

- Evidence source: live public probing against `https://api.alphaxiv.org` on
  May 9, 2026, plus `docs/api-inventory.md`.
- `GET /papers/v3/{identifier}` is public and returns a direct paper-version
  payload. Live probe `GET /papers/v3/2603.04379` returned `HTTP 200` with an
  object containing `groupId`, `versionId`, `universalId`, `title`,
  `abstract`, `versionLabel`, `versionOrder`, `resources`, `versions`,
  `citationBibtex`, `citationsCount`, and source/uploader fields. For
  `2603.04379`, the payload included `groupId`
  `019cbc05-f11c-75c7-a13b-b028107d6a76`, `versionId`
  `019cbc05-f158-7e3a-b9c1-a43274c0130b`, and title `Helios: Real Real-Time
  Long Video Generation Model`.
- `GET /papers/v3/{identifier}` also accepts a paper-version UUID. Live probe
  `GET /papers/v3/019cbc05-f158-7e3a-b9c1-a43274c0130b` returned `HTTP 200`
  with the same direct paper-version shape and the same `groupId`,
  `versionId`, `universalId`, and title as the arXiv-ID probe.
- `GET /papers/v3/legacy/{identifier}` remains public for legacy paper
  resolution by arXiv ID. Live probe `GET /papers/v3/legacy/2603.04379`
  returned `HTTP 200` with top-level `paper` and `comments`; nested
  `paper.paper_version.id` was `019cbc05-f158-7e3a-b9c1-a43274c0130b`, and
  nested `paper.paper_group.id` was `019cbc05-f11c-75c7-a13b-b028107d6a76`.
- `GET /papers/v3/{identifier}/preview` is public and returns a compact paper
  preview payload. Live probe `GET /papers/v3/2603.04379/preview` returned
  `HTTP 200` with an object containing `id`, `paper_group_id`, `version_id`,
  `canonical_id`, `universal_paper_id`, `title`, `abstract`, `paper_summary`,
  `image_url`, `authors`, `full_authors`, `author_info`, `topics`,
  `metrics`, `github_url`, and `github_stars`.
- `GET /papers/v3/{paperGroupId}/figures` is public and returns an object with
  a `figures` array. Live probe
  `GET /papers/v3/015c9ef4-ac30-768d-928b-847320902575/figures` returned
  `HTTP 200` with eight entries; the first entry was
  `figures/1706.03762v7/ModalNet-19.png`. Live probe
  `GET /papers/v3/019cbc05-f11c-75c7-a13b-b028107d6a76/figures` returned
  `HTTP 200` with an empty `figures` array, so empty figure lists are valid.

## Identifier Behavior

- Existing arXiv identifier behavior is preserved. Bare arXiv IDs such as
  `2603.04379` and versioned IDs such as `2603.04379v1` continue to resolve
  through `/papers/v3/legacy/{identifier}` where legacy metadata or comments
  are needed.
- Existing UUID behavior is preserved. Paper-version UUIDs may be used directly
  for endpoints that are scoped to a paper version, and paper-group UUIDs may
  be used directly for endpoints scoped to a paper group.
- Direct paper resolution uses `/papers/v3/{identifier}` as a public fallback
  when legacy arXiv resolution is not the right route for the caller's
  identifier. This fallback accepts alphaXiv direct identifiers, including
  paper-version UUIDs, and any alphaXiv slug that the public direct paper
  endpoint accepts.
- Direct fallback success must populate the same resolver aliases the current
  SDK relies on where the payload provides enough information: requested
  identifier, `universalId`, canonical versioned arXiv ID
  `universalId` + `v` + `versionOrder`, `versionId`, and `groupId`.
- Direct fallback failure must not guess alternate route shapes. If both the
  preserved route and the direct fallback fail, the SDK raises the existing
  resolution error type with enough context for the user to see which
  identifier failed.
- Preview accepts the same user-facing paper identifiers as paper resolution,
  but calls `/papers/v3/{identifier}/preview` once the endpoint-compatible
  identifier is known.
- Figures requires a paper-group UUID at the HTTP layer. Public SDK and CLI
  entrypoints may accept arXiv IDs, paper-version UUIDs, or accepted alphaXiv
  slugs, but they must resolve them to `paperGroupId` before calling
  `/papers/v3/{paperGroupId}/figures`.

## SDK And CLI Surface

- Python SDK adds `client.papers.preview(identifier)` returning a typed preview
  object with raw payload retention.
- Python SDK adds `client.papers.figures(identifier)` returning a typed figures
  result containing the resolved `paper_group_id` and a list of figure asset
  paths.
- Python SDK direct resolution accepts alphaXiv slugs through the direct paper
  fallback without breaking current arXiv and UUID resolution.
- CLI adds `alphaxiv paper preview <identifier>` and supports the current paper
  context where existing paper commands already support it.
- CLI adds `alphaxiv paper figures <identifier>` and supports the current paper
  context where existing paper commands already support it.
- CLI preview output includes stable metadata fields suitable for scripting:
  title, canonical arXiv ID, universal paper ID, paper group ID, version ID,
  authors, topics, metrics, image path, GitHub URL/stars when present, and
  raw JSON output.
- CLI figures output includes paper group ID and figure paths. Empty figure
  lists must render as an empty result, not as an error.

## Acceptance Criteria

- Python users can request a compact paper preview for any supported paper
  identifier without fetching comments, full text, overview text, or similar
  papers.
- Python users can request paper figures by arXiv ID, paper-version UUID,
  paper-group UUID, or accepted alphaXiv slug; the SDK resolves non-group
  identifiers before calling the figures endpoint.
- Python users can resolve an alphaXiv slug through the public direct paper
  endpoint when legacy arXiv resolution is unavailable.
- Existing paper metadata, comments, resources, overview, full-text, similar,
  vote, and view behavior remain unchanged unless explicitly updated by a later
  accepted implementation spec.
- CLI users can run preview and figures commands with an explicit identifier or
  current paper context where supported.
- SDK and CLI errors distinguish unsupported identifier shape from live
  endpoint `404`/API failures using the existing exception style.
- Tests cover arXiv ID, paper-version UUID, direct fallback, empty figures, and
  non-empty figures payload handling without requiring live network by default.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest
ALPHAXIV_RUN_E2E=1 uv run pytest tests/e2e -q
```
