# Auth, Folders, And Social Actions

## Status

Status: Implemented

Owner issue: PET-12 records the existing implementation.

This spec records the current implemented folder, vote, view, and comment-action
surface. PET-12 is documentation-only and does not change SDK or CLI behavior.

## SDK Surface

- `AlphaXivClient.from_saved_api_key(...)` creates an authenticated client from
  `ALPHAXIV_API_KEY` or the locally saved API key.
- `AlphaXivClient.from_api_key(api_key, ...)` creates an authenticated client
  from an explicit API key.
- `AlphaXivClient.from_authorization(authorization, ...)` creates an
  authenticated client from an explicit bearer authorization header.
- `AlphaXivClient.from_saved_browser_auth(...)` and
  `AlphaXivClient.from_saved_auth(...)` support browser-backed auth for flows
  that need a web-session authorization header.
- `client.folders.list()` calls the authenticated folder listing endpoint and
  returns `list[Folder]`.
- `client.folders.get(selector)` resolves one folder from the list by id, exact
  case-insensitive name, partial name, or id prefix.
- `client.folders.add_papers(folder, paper_group_ids)` resolves the folder,
  posts deduped non-empty paper group ids, and returns the refreshed `Folder`.
- `client.folders.remove_papers(folder, paper_group_ids)` resolves the folder,
  posts deduped non-empty paper group ids, and returns the refreshed `Folder`.
- `client.papers.create_comment(identifier, body=..., title=None,
  tag="general")` creates a top-level paper comment.
- `client.papers.reply_to_comment(identifier, parent_comment_id, body=...,
  title=None, tag="general")` creates a reply by setting `parentCommentId`.
- `client.comments.toggle_upvote(comment_id)` toggles an authenticated comment
  upvote and returns the endpoint payload when present.
- `client.comments.delete(comment_id)` deletes one authenticated comment by id.
- `client.papers.toggle_vote(identifier)` toggles the authenticated vote state
  for the resolved paper group id.
- `client.papers.record_view(identifier)` records an authenticated paper view
  for the resolved paper group id.

## CLI Surface

- `alphaxiv auth status|set-api-key|clear|login-web|clear-web` manages or
  inspects saved API-key and browser-backed credentials.
- `alphaxiv folders list [--papers] [--raw|--json]` lists authenticated folders
  and optionally renders nested paper rows.
- `alphaxiv folders show <folder> [--raw|--json]` resolves one folder selector
  and renders the full saved-paper list.
- `alphaxiv paper folders list [paper-id] [--raw|--json]` resolves a paper group
  id and shows whether each authenticated folder contains that paper.
- `alphaxiv paper folders add [paper-id] <folder> [--yes]` saves a paper into a
  folder after confirmation unless `--yes` is provided.
- `alphaxiv paper folders remove [paper-id] <folder> [--yes]` removes a paper
  from a folder after confirmation unless `--yes` is provided.
- `alphaxiv paper comments add [paper-id] --body <text> [--title <text>]
  [--tag <tag>]` creates a top-level authenticated comment.
- `alphaxiv paper comments reply [paper-id] <comment-id> --body <text>
  [--title <text>] [--tag <tag>]` creates an authenticated reply.
- `alphaxiv paper comments upvote <comment-id> [--yes]` toggles comment upvote
  state after confirmation unless `--yes` is provided.
- `alphaxiv paper comments delete <comment-id> [--yes]` deletes a comment after
  confirmation unless `--yes` is provided.
- `alphaxiv paper vote [paper-id] [--yes]` toggles paper vote state after
  confirmation unless `--yes` is provided.
- `alphaxiv paper view [paper-id] [--yes]` records a paper view after
  confirmation unless `--yes` is provided.

Commands with optional `[paper-id]` use the saved current paper context when the
argument is omitted. `--json` emits normalized JSON through
`src/alphaxiv/cli/serialize.py`; `--raw` emits endpoint payloads with only the
small amount of local context needed by the command.

## Endpoint Evidence

- Evidence source: `docs/api-inventory.md`, "User and Preferences", "Voting and
  Social Actions", "Papers", and "Routes Currently Used By This Repository".
- Implementation source: `src/alphaxiv/_folders.py`,
  `src/alphaxiv/_comments.py`, `src/alphaxiv/_papers.py`,
  `src/alphaxiv/cli/folders.py`, and `src/alphaxiv/cli/paper.py`.
- Test evidence: folder, paper-folder, comment, vote, and view cases in
  `tests/unit/test_cli_endpoints.py`; folder/comment live helpers in
  `tests/e2e/helpers.py`.
- `GET /users/v3` reads current user profile and preferences.
- `PATCH /users/v3/preferences` writes user preferences.
- `GET /folders/v3` reads authenticated folder and bookmark containers.
- `POST /folders/v3/{folderId}/add-papers` adds one or more paper group ids to
  an authenticated folder.
- `POST /folders/v3/{folderId}/remove-papers` removes one or more paper group
  ids from an authenticated folder.
- `POST /papers/v2/{paperVersionId}/comment` creates top-level paper comments
  and replies. The current web schema requires nullable annotation fields even
  when the SDK/CLI expose only text comments.
- `POST /papers/v3/{paperGroupId}/view` records a paper view.
- `POST /papers/v3/{paperGroupId}/like?liked={true|false}` sets a paper vote.
- `POST /comments/v2/{commentId}/upvote` toggles a comment upvote.
- `DELETE /comments/v2/{commentId}` deletes a comment.

## Auth Evidence

- `AlphaXivClient(api_key=...)` builds a bearer `Authorization` header from an
  API key, while `AlphaXivClient(authorization=...)` accepts an explicit bearer
  header for browser-backed sessions and other non-API-key tokens.
- `AlphaXivClient.from_saved_api_key()` loads the effective API key from
  `ALPHAXIV_API_KEY` or the local saved key and fails before constructing a
  client when neither exists.
- `AlphaXivClient.from_saved_browser_auth()` loads or refreshes the saved
  browser-backed bearer auth and fails before constructing a client when no
  usable browser auth exists.
- `AlphaXivClient.from_saved_auth(prefer_browser=True)` prefers saved browser
  auth and falls back to API-key auth; without `prefer_browser`, API-key auth is
  tried first.
- CLI `make_client()` uses the effective API key only. CLI
  `make_assistant_client()` prefers non-expired saved browser auth and falls
  back to API-key auth, matching the current assistant write workaround.
- `resolve_api_key()` gives `ALPHAXIV_API_KEY` precedence over the local
  `${ALPHAXIV_HOME:-~/.alphaxiv}/api-key.json` file.
- `auth set-api-key` validates the supplied key against `GET /users/v3` before
  saving `api-key.json` with owner-only permissions.
- `auth login-web` opens a persistent Playwright profile under
  `${ALPHAXIV_HOME:-~/.alphaxiv}/browser-profile`, extracts an alphaXiv web
  token from local storage or Clerk session state, validates it with
  `GET /users/v3`, and saves `${ALPHAXIV_HOME:-~/.alphaxiv}/auth.json` with
  owner-only permissions.
- Expired saved browser auth is refreshed from the persistent browser profile
  when possible; if refresh fails, assistant client construction falls back to
  API-key auth.
- `auth status` reports both API-key and browser-backed auth state, including
  source, token prefix, user metadata, and expiry where available.
- `auth clear` removes only `api-key.json`; `auth clear-web` removes only
  `auth.json` unless `--clear-browser-profile` is supplied.

## Local Context Evidence

- Paper CLI context is stored at
  `${ALPHAXIV_HOME:-~/.alphaxiv}/context.json` as a serialized `ResolvedPaper`.
- `context use paper <paper-id>` resolves the paper through the public paper
  resolver before saving the current paper context.
- `context show paper` best-effort hydrates a missing saved title by reading the
  current paper through the public paper endpoint and then rewriting the saved
  context with the title.
- Paper commands that accept optional paper ids use explicit arguments first and
  fall back to the saved paper context through `get_effective_identifier()`.
- `context show` prints or serializes both current paper context and current
  assistant context; `context show paper` and `context show assistant` target
  one local context file.
- `context clear paper` removes only `context.json`; bare `context clear`
  removes both `context.json` and `assistant-context.json`.

| Method | Path | SDK/CLI use | Body |
| --- | --- | --- | --- |
| `GET` | `/folders/v3` | `folders.list`, `folders.get`, `alphaxiv folders list`, `alphaxiv folders show`, `alphaxiv paper folders list` | none |
| `POST` | `/folders/v3/{folderId}/add-papers` | `folders.add_papers`, `alphaxiv paper folders add` | `{"paperGroupIds": [...]}` |
| `POST` | `/folders/v3/{folderId}/remove-papers` | `folders.remove_papers`, `alphaxiv paper folders remove` | `{"paperGroupIds": [...]}` |
| `POST` | `/papers/v2/{paperVersionId}/comment` | `papers.create_comment`, `papers.reply_to_comment`, `alphaxiv paper comments add`, `alphaxiv paper comments reply` | `body`, optional `title`, `tag`, optional `parentCommentId`, nullable annotation fields |
| `POST` | `/papers/v3/{paperGroupId}/view` | `papers.record_view`, `alphaxiv paper view` | none |
| `POST` | `/papers/v3/{paperGroupId}/like?liked={true|false}` | `papers.toggle_vote`, `alphaxiv paper vote` | query `liked` after reading `/users/v3` `votedPaperGroups` |
| `POST` | `/comments/v2/{commentId}/upvote` | `comments.toggle_upvote`, `alphaxiv paper comments upvote` | none |
| `DELETE` | `/comments/v2/{commentId}` | `comments.delete`, `alphaxiv paper comments delete` | none |

## Inputs And Outputs

- Folder selectors must be non-empty. They may be folder ids, exact
  case-insensitive names, partial names, or id prefixes.
- Ambiguous folder selectors raise an error listing the matched folder ids and
  names.
- Folder add/remove normalizes `paper_group_ids` by trimming whitespace,
  dropping blanks, and deduplicating while preserving order.
- Folder add/remove requires at least one normalized paper group id.
- Paper-folder CLI mutations accept either `<folder>` with saved paper context
  or `<paper-id> <folder>`.
- Paper-folder operations require a bare or versioned arXiv id that can resolve
  to a paper group id; paper-version UUID inputs are not sufficient.
- Comment tags are constrained to `anonymous`, `general`, `personal`,
  `research`, and `resources`.
- Comment creation trims the body and rejects empty bodies before sending a
  request.
- Comment creation sends only text fields plus optional parent id. Annotation
  editing is intentionally not exposed.
- Vote and view operations require a bare or versioned arXiv id that resolves
  to a paper group id.
- Comment upvote and paper vote/view methods return `None`, a decoded response
  object, or a fallback `{"text": ...}` / `{"data": ...}` wrapper depending on
  the endpoint response body.
- Comment delete returns `None` after the request succeeds.

## Acceptance Criteria

- API-key auth can be loaded from `ALPHAXIV_API_KEY` or the local saved key.
- Browser-backed auth can be captured and reused for web-session-backed flows.
- Python users can list folders, resolve folders, add or remove papers from
  folders, and perform the existing paper and comment social actions with
  authenticated clients.
- CLI users can inspect auth status, save or clear auth, list folders, inspect
  paper-folder membership, add or remove a paper from a folder, create or reply
  to comments, upvote comments, delete comments, record views, and vote on
  papers through the existing grouped commands.
- Mutating CLI commands keep their existing confirmation prompts unless `--yes`
  is provided.
- Comment creation remains text-first and does not expose unsupported annotation
  editing behavior.
- Existing auth precedence, saved auth files, browser profile behavior, and clear
  semantics are documented.
- Existing paper context storage, paper-context fallback, context show, and
  context clear behavior are documented.
- PET-12 makes no SDK or CLI behavior changes.

## Validation Commands

```bash
uv run python scripts/check_specs.py
uv run pytest tests/unit/test_auth.py tests/unit/test_cli_endpoints.py -q
uv run pytest tests/unit/test_cli_context.py -q
uv run pytest tests/integration/test_client.py -q
uv run pytest tests/unit -q
uv run pytest
```
