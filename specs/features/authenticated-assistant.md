# Authenticated Assistant

## Status

Status: Implemented

Owner issue: pre-existing implementation before PET-8.

This spec records the current implemented surface; PET-8 does not change SDK or
CLI behavior.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "Assistant", "User and
  Preferences", and "Routes Currently Used By This Repository".
- `GET /assistant/v2?variant=homepage` lists homepage assistant sessions.
- `GET /assistant/v2?variant=paper&paperVersion={paperVersionId}` lists
  paper-scoped assistant sessions.
- `GET /assistant/v2/{sessionId}/messages` reads structured assistant history.
- `POST /assistant/v2/chat` starts or continues an authenticated assistant chat
  and returns SSE output.
- `GET /assistant/v2/url-metadata?url=...` reads link metadata.
- `GET /users/v3` reads the current preferred assistant model.
- `PATCH /users/v3/preferences` updates the preferred assistant model.

## Acceptance Criteria

- Assistant methods require authentication and raise the existing auth error
  behavior without saved credentials.
- Browser-backed auth remains available for assistant chat writes when API-key
  chat writes are restricted.
- Python users can list sessions, read history, fetch URL metadata, read or set
  the preferred model, and start or continue homepage and paper-scoped chats.
- CLI users can access assistant list, history, model, URL metadata, start, and
  reply commands without changing command names in PET-8.
- The client does not claim a trusted live model catalog.

## Validation Commands

```bash
uv run pytest tests/unit/test_assistant.py -q
uv run pytest tests/unit/test_auth.py -q
uv run python scripts/check_specs.py
```

