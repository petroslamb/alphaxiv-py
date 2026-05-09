# Public Read Expansion

## Status

Status: Proposed

Owner issue: future Phase 2 issue.

This spec is a placeholder for confirmed new public read endpoints. PET-8 does
not accept or implement any new endpoint behavior.

## Endpoint Evidence

- Evidence source required before acceptance: `docs/api-inventory.md` plus the
  future Phase 2 issue notes that confirm live public-read behavior.
- Candidate evidence must identify method, path, access level, payload shape,
  and whether the route is public without auth.
- Known expansion candidates include public people, organization detail, profile,
  and additional read-only discovery surfaces, but none are accepted by this
  placeholder.

## Acceptance Criteria

- A future PR may move this spec from Proposed to Accepted only after endpoint
  evidence is concrete enough to implement from.
- The accepted spec must separate public read behavior from authenticated write
  or account-specific behavior.
- The accepted spec must define Python API names, CLI command names if any,
  output shape, error handling, and validation coverage before implementation.
- Phase 3 implementation must not add behavior beyond the accepted public read
  spec.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest
```

