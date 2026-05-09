# Feature Name

## Status

Status: Proposed

Owner issue: PET-XX

No SDK or CLI behavior may ship for this surface until this spec is accepted.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`
- Endpoint: `GET /example/path`
- Access: public
- Evidence status: confirmed from live traffic, direct probing, or accepted
  follow-up issue notes.

## Acceptance Criteria

- The client behavior is described in user-facing terms.
- Auth, pagination, errors, and output shape are documented when relevant.
- CLI behavior is documented when the surface has a CLI command.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest
```

