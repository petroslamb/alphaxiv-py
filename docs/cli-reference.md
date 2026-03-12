# CLI Reference

## Context

```bash
alphaxiv login --api-key "$ALPHAXIV_API_KEY"
alphaxiv login
alphaxiv use 1706.03762
alphaxiv status
alphaxiv logout
alphaxiv clear
```

`login --api-key <key>` validates and saves an explicit alphaXiv API key to `auth.json`.

`login` without `--api-key` opens a visible browser profile under `ALPHAXIV_HOME`, waits for you to complete the alphaXiv sign-in flow, then saves the currently available bearer token to `auth.json`.

Browser support is optional. Install it only if you need browser login:

```bash
uv sync --extra browser
uv run playwright install chromium
```

This flow launches visible Chromium. A headless browser is not required for normal API-key usage.

`logout` removes the saved bearer token. Add `--clear-browser-profile` if you also want to remove the cached Playwright browser profile.

`status` prints auth loaded from `ALPHAXIV_API_KEY` or `auth.json`, plus the current paper context and current assistant session context when present.

## Search

```bash
alphaxiv search "attention is all you need"
```

The homepage-style search command prints paper matches plus suggested topics and organization matches when available.

### Individual Search Endpoints

```bash
alphaxiv search-papers "attention is all you need"
alphaxiv search-organizations "attention is all you need"
alphaxiv search-topics "attention is all you need"
```

- `search-papers` calls only the public paper search endpoint.
- `search-organizations` calls only the public organization search endpoint.
- `search-topics` calls only the public closest-topic endpoint.

## Feed

```bash
alphaxiv feed filters
alphaxiv feed list --sort hot --limit 10
alphaxiv feed list --sort likes --limit 5
alphaxiv feed list --organization MIT --source twitter --interval 30-days --limit 5
alphaxiv feed list --category computer-science --custom-category generative-models --limit 5
```

Supported `feed list` options mirror the public homepage as closely as the anonymous site allows:

- `--sort hot|likes`
- `--organization <name>` repeatable
- `--menu-category "<homepage category>"` repeatable
- `--category <slug>` repeatable
- `--subcategory <slug>` repeatable
- `--custom-category <slug>` repeatable
- `--source github|twitter`
- `--interval 3-days|7-days|30-days|90-days|all-time`
- `--limit <n>`

## Paper Metadata

```bash
alphaxiv paper show 1706.03762
alphaxiv paper text 1706.03762 --page 1
alphaxiv overview 1706.03762
alphaxiv overview 1706.03762 --machine
alphaxiv overview-status 1706.03762
alphaxiv resources 1706.03762
alphaxiv resources 1706.03762 --bibtex
alphaxiv resources 1706.03762 --transcript
```

If the paper ID is omitted, the CLI uses the current paper from context.

`paper text` calls the public full-text endpoint for the resolved paper version UUID.

- Without `--page`, it prints every page in order.
- `--page <n>` is repeatable and limits output to specific 1-based pages.

`overview --machine` prints only the raw machine-readable markdown shown behind the overview page's `Machine` toggle.

`overview-status` calls the public overview status endpoint and prints the generation state plus available translation languages.

`resources --bibtex` prints the paper's BibTeX citation when alphaXiv exposes one.

`resources --transcript` prints the AI audio summary transcript when the paper has a public podcast transcript.

## PDF Helpers

```bash
alphaxiv pdf url 1706.03762
alphaxiv pdf download 1706.03762 ./paper.pdf
```

## Assistant

```bash
alphaxiv assistant list
alphaxiv assistant set-model "Claude 4.6 Sonnet"
alphaxiv assistant start "Find papers on agent frameworks"
alphaxiv assistant start --model "GPT 5.4" "Find papers on agent frameworks"
alphaxiv assistant reply "Focus on the most cited ones"
alphaxiv assistant history
alphaxiv assistant use <session-id>
alphaxiv assistant clear
```

The assistant uses authenticated `assistant/v2` endpoints and streams responses over `text/event-stream`.

`assistant list` defaults to homepage chats. Add `--paper <paper-id>` to list paper-scoped chats for a specific paper.

`assistant set-model <label-or-id>` persists the preferred assistant model through `PATCH /users/v3/preferences`.

The CLI does not claim to know the full live model catalog. It reads the current preferred model from `GET /users/v3` and accepts explicit ids or label-like input without local catalog validation.

`assistant start` options:

- `--paper <paper-id>` starts a paper-scoped chat
- `--model <label-or-id>` overrides the model for that request without changing the saved preference
- `--web-search off|full`
- `--thinking / --no-thinking`
- `--raw` prints raw SSE event payloads instead of the friendly renderer

`assistant reply` accepts either:

- `alphaxiv assistant reply "next question"` to use the saved current assistant chat
- `alphaxiv assistant reply <session-id> "next question"` to target a specific session

`assistant reply` also accepts `--model <label-or-id>` for a one-off model override.

`assistant history` accepts an optional session id. Without one, it uses the saved current assistant chat.

`assistant use <session-id>` sets the saved current assistant chat. If the session belongs to the current paper context, that paper association is saved too.

This assistant surface is distinct from the public homepage `search` command:

- `search` calls public paper, topic, and organization search endpoints
- `assistant` calls the authenticated alphaXiv assistant and can invoke internal tools such as embedding similarity search and paper retrieval
