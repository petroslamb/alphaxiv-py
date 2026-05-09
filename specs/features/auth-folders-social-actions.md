# Auth, Folders, And Social Actions

## Status

Status: Implemented

Owner issue: pre-existing implementation before PET-8.

This spec records the current implemented surface; PET-8 does not change SDK or
CLI behavior.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "User and Preferences", "Voting and
  Social Actions", "Papers", and "Routes Currently Used By This Repository".
- `GET /users/v3` reads current user profile and preferences.
- `PATCH /users/v3/preferences` writes user preferences.
- `GET /folders/v3` reads authenticated folder and bookmark containers.
- `POST /papers/v2/{paperVersionId}/comment` creates top-level paper comments
  and replies.
- `POST /papers/v3/{paperGroupId}/view` records a paper view.
- `POST /v2/papers/{paperId}/vote` toggles a paper vote.
- `POST /comments/v2/{commentId}/upvote` toggles a comment upvote.
- `DELETE /comments/v2/{commentId}` deletes a comment.

## Acceptance Criteria

- API-key auth can be loaded from `ALPHAXIV_API_KEY` or the local saved key.
- Browser-backed auth can be captured and reused for web-session-backed flows.
- Python users can list folders and perform the existing paper and comment
  social actions with authenticated clients.
- CLI users can inspect auth status, save or clear auth, list folders, create or
  reply to comments, upvote comments, delete comments, record views, and vote on
  papers through the existing grouped commands.
- Comment creation remains text-first and does not expose unsupported annotation
  editing behavior.

## Validation Commands

```bash
uv run pytest tests/unit/test_auth.py tests/unit/test_cli_endpoints.py -q
uv run pytest tests/integration/test_client.py -q
uv run python scripts/check_specs.py
```

