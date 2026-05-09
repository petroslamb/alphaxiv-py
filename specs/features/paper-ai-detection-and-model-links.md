# Paper AI Detection And Model Links

## Status

Status: Accepted

Owner issue: PET-14

This Phase 2b spec accepts the public paper AI-detection and model-link
sidecar endpoints for future implementation. PET-14 does not change SDK or CLI
behavior.

## Endpoint Evidence

- Evidence source: live direct probes against `https://api.alphaxiv.org` on
  2026-05-09, plus `docs/api-inventory.md`.
- `GET /papers/v3/{paperVersion}/ai-detection` is public and requires an
  alphaXiv UUIDv7 paper-version ID at the HTTP layer.
- `GET /papers/v3/{paperVersion}/model-links` is public and requires an
  alphaXiv UUIDv7 paper-version ID at the HTTP layer.
- `paperVersion=019e057a-354c-7480-afd1-a79e18674c1e` returned `200` for
  `/ai-detection` with top-level keys `state`, `headline`,
  `predictionShort`, `fractionHuman`, `fractionAi`, `fractionAiAssisted`,
  `windows`, and `updatedAt`. The payload had `state: "done"`,
  `headline: "Mostly Human Written"`, `predictionShort: "Human"`,
  59 `windows`, and the first window included `text`, `label`,
  `aiAssistanceScore`, `confidence`, `pageIndex`, `startIndex`, and
  `endIndex`.
- `paperVersion=019cbc05-f158-7e3a-b9c1-a43274c0130b` returned `404` for
  `/ai-detection` with `{"error":{"message":"Ai detection not found",
  "collection":"ai detection"}}`.
- `paperVersion=019e057a-354c-7480-afd1-a79e18674c1e` returned `200` for
  `/model-links` with top-level keys `state`, `matches`, `updatedAt`, and
  `isOutdated`. The payload had `state: "done"`, 26 `matches`, and the first
  match included `matchedText`, `pageIndex`, `startIndex`, `endIndex`, and a
  nested `model` object with `id`, `modelId`, `providerName`, `modelName`,
  `description`, `releaseDate`, and `categoryRankings`.
- `paperVersion=019cbc05-f158-7e3a-b9c1-a43274c0130b` returned `200` for
  `/model-links` with `state: "done"`, 29 `matches`, `updatedAt`, and
  `isOutdated: false`.
- `paperVersion=01900000-0000-7000-8000-000000000000` returned `404` for
  `/model-links` with `{"error":{"message":"Paper model links not found",
  "collection":"paper model links"}}`.
- A bare arXiv ID such as `2605.06651` returned `400` for both sidecar routes
  because the route validates `param.paperVersion` as a UUIDv7. SDK and CLI
  support must resolve bare or versioned arXiv IDs through the existing paper
  resolver before calling these sidecar endpoints.

## Output Shape

Future implementation must expose typed outputs that preserve the live payload
without guessing undocumented fields:

- `PaperAiDetection`: `state: str`, `headline: str | None`,
  `prediction_short: str | None`, `fraction_human: float | None`,
  `fraction_ai: float | None`, `fraction_ai_assisted: float | None`,
  `windows: list[AiDetectionWindow]`, `updated_at: int | None`.
- `AiDetectionWindow`: `text: str`, `label: str | None`,
  `ai_assistance_score: float | None`, `confidence: str | None`,
  `page_index: int | None`, `start_index: int | None`,
  `end_index: int | None`.
- `PaperModelLinks`: `state: str`, `matches: list[PaperModelLinkMatch]`,
  `updated_at: int | None`, `is_outdated: bool | None`.
- `PaperModelLinkMatch`: `matched_text: str`, `page_index: int | None`,
  `start_index: int | None`, `end_index: int | None`,
  `model: LinkedModel | None`.
- `LinkedModel`: `id: str | None`, `model_id: str | None`,
  `provider_name: str | None`, `model_name: str | None`,
  `description: str | None`, `release_date: int | None`,
  `category_rankings: list[Any]`.

The JSON form must use the API's camelCase field names when returned through
`--json`: `predictionShort`, `fractionHuman`, `fractionAi`,
`fractionAiAssisted`, `updatedAt`, `aiAssistanceScore`, `pageIndex`,
`startIndex`, `endIndex`, `isOutdated`, `matchedText`, `modelId`,
`providerName`, `modelName`, `releaseDate`, and `categoryRankings`.

## Identifier And Error Behavior

- Python methods must accept bare arXiv IDs, versioned arXiv IDs, and
  paper-version UUIDs. Bare and versioned IDs must resolve to the
  paper-version UUID before the sidecar request.
- Invalid identifiers must continue to raise `ResolutionError` before sending a
  sidecar request when the input cannot be resolved locally or through
  `/papers/v3/legacy/{id}`.
- HTTP `404` for missing AI-detection data is no-data, not a transport failure.
  The Python method must return `None`.
- HTTP `404` for missing model-link data is no-data, not a transport failure.
  The Python method must return `None`.
- HTTP `400` from the sidecar route should only be possible for direct invalid
  UUID calls; expose it as `APIError` if it escapes identifier resolution.
- Empty `windows` or empty `matches` arrays are valid completed payloads and
  must not be converted to `None`.

## SDK And CLI Surface

- Python SDK methods: `client.papers.ai_detection(identifier)` and
  `client.papers.model_links(identifier)`.
- CLI reads: `alphaxiv paper ai-detection PAPER_ID` and
  `alphaxiv paper model-links PAPER_ID`.
- CLI commands should also accept the current paper context where existing
  paper read commands support context.
- Default CLI rendering for AI detection should show state, headline,
  prediction, human/AI/AI-assisted fractions, updated time, and a compact
  window table with label, confidence, score, page, and character range.
- Default CLI rendering for model links should show state, outdated status,
  updated time, match count, and a compact match table with matched text, page,
  character range, provider, model name, and model ID.
- When a no-data `404` maps to `None`, default CLI rendering should print a
  concise no-data message and exit successfully. `--json` should print `null`.

## Acceptance Criteria

- Python users can retrieve paper AI-detection data for a bare arXiv ID,
  versioned arXiv ID, or paper-version UUID when the sidecar exists.
- Python users receive `None` for confirmed no-data `404` responses from
  AI-detection and model-link sidecars.
- Python users can retrieve model-link matches, including nested model metadata,
  without losing unknown category-ranking payloads.
- CLI users can render both sidecars in human-readable tables and can request
  the exact JSON-compatible shape with `--json`.
- CLI no-data responses are successful, concise, and distinct from invalid
  identifier or transport failures.
- Implementation tests cover successful payloads, no-data `404`, identifier
  resolution, JSON rendering, and human-readable CLI rendering for both
  sidecars.
- No Phase 3 implementation may ship beyond the SDK and CLI surfaces accepted
  in this spec.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest
```
