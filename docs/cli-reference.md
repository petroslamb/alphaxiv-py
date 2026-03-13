# CLI Reference

The CLI is organized around resource groups:

- `alphaxiv auth`
- `alphaxiv context`
- `alphaxiv search`
- `alphaxiv feed`
- `alphaxiv paper`
- `alphaxiv assistant`
- `alphaxiv folders`

## Auth

```bash
alphaxiv auth set-api-key --api-key "$ALPHAXIV_API_KEY"
alphaxiv auth status
alphaxiv auth clear
```

`auth set-api-key --api-key <key>` validates and saves an explicit alphaXiv API key to
`api-key.json`.

`auth set-api-key` without `--api-key` prompts for the API key with hidden input before
validating and saving it.

`auth status` prints auth loaded from `ALPHAXIV_API_KEY` or `api-key.json`.

`auth clear` removes the locally saved `api-key.json`.

## Context

```bash
alphaxiv context show
alphaxiv context show paper
alphaxiv context show assistant
alphaxiv context use paper 1706.03762
alphaxiv context use assistant <session-id>
alphaxiv context clear
alphaxiv context clear paper
alphaxiv context clear assistant
```

`context show` prints both the current paper context and current assistant context.

`context show paper` best-effort refreshes a missing saved paper title when the context file has a
bare or versioned arXiv id but no title yet.

`context use paper <paper-id>` resolves a paper identifier and saves it as the current paper
context for later commands.

`context use assistant <session-id>` saves the current assistant chat. If the session belongs to
the current paper context, that paper association is saved too.

`context clear` removes both saved contexts. Use `context clear paper` or `context clear
assistant` to target only one file.

## Search

```bash
alphaxiv search all "attention is all you need"
alphaxiv search papers "attention is all you need"
alphaxiv search organizations "attention is all you need"
alphaxiv search topics "attention is all you need"
```

`search all` performs the homepage-style search and prints paper matches plus suggested topics and
organization matches when available.

`search papers` calls only the public paper search endpoint.

`search organizations` calls only the public organization search endpoint.

`search topics` calls only the public closest-topic endpoint.

## Feed

```bash
alphaxiv feed filters
alphaxiv feed filters search "agentic"
alphaxiv feed list --sort hot --limit 10
alphaxiv feed list --sort likes --limit 5
alphaxiv feed list --organization MIT --source twitter --interval 30-days --limit 5
alphaxiv feed list --category computer-science --custom-category generative-models --limit 5
alphaxiv feed list --topic agentic-frameworks --organization Meta --limit 5
alphaxiv feed list --source github --sort most-stars --limit 5
```

`feed filters search` mirrors the website filter drawer search box by querying live topic and
organization filters.

Supported `feed list` options mirror the public homepage feed API:

- `--sort hot|likes|github|twitter|most-stars|most-twitter-likes`
- `--organization <name>` repeatable
- `--menu-category "<homepage category>"` repeatable
- `--category <slug>` repeatable
- `--subcategory <slug>` repeatable
- `--custom-category <slug>` repeatable
- `--topic <slug-or-code>` repeatable
- `--source github|twitter`
- `--interval 3-days|7-days|30-days|90-days|all-time`
- `--limit <n>`

`--topic` is the closest match to the live website's internal feed filtering, because the site
ultimately resolves many drawer selections down to raw topic values before calling
`/papers/v3/feed`.

## Paper

```bash
alphaxiv paper show 1706.03762
alphaxiv paper abstract 1706.03762
alphaxiv paper summary 1706.03762
alphaxiv paper overview 1706.03762
alphaxiv paper overview-status 1706.03762
alphaxiv paper resources 1706.03762
alphaxiv paper resources 1706.03762 --bibtex
alphaxiv paper resources 1706.03762 --transcript
alphaxiv paper comments list 1706.03762
alphaxiv paper comments add 1706.03762 --body "Helpful note"
alphaxiv paper comments reply 1706.03762 <comment-id> --body "Thanks"
alphaxiv paper comments upvote <comment-id> --yes
alphaxiv paper comments delete <comment-id> --yes
alphaxiv paper similar 1706.03762 --limit 5
alphaxiv paper text 1706.03762 --page 1
alphaxiv paper pdf url 1706.03762
alphaxiv paper pdf download 1706.03762 ./paper.pdf
alphaxiv paper vote 1706.03762 --yes
alphaxiv paper view 1706.03762 --yes
```

If the paper id is omitted, every optional `[paper-id]` command uses the current paper from
context.

`paper abstract` prints the paper title and abstract from the main paper metadata payload.

`paper summary` prints the structured AI summary from the overview endpoint. Add
`--language <code>` to request a translated summary, or `--raw` to print the raw structured
summary payload.

`paper overview --machine` prints only the raw machine-readable markdown shown behind the overview
page's `Machine` toggle.

`paper overview-status` calls the public overview status endpoint and prints the generation state
plus available translation languages.

`paper resources --bibtex` prints the paper's BibTeX citation when alphaXiv exposes one.

`paper resources --transcript` prints the AI audio summary transcript when the paper has a public
podcast transcript.

`paper comments list` calls the public comments endpoint and renders the nested thread. Add `--raw`
to print the raw JSON payload.

`paper comments add` creates a top-level authenticated comment. It requires `--body`, accepts
optional `--title`, and supports the confirmed tag set:
`anonymous`, `general`, `personal`, `research`, `resources`.

`paper comments reply` posts an authenticated reply to an existing comment id. It accepts either
`<comment-id>` with current paper context or `<paper-id> <comment-id>` when you want to be
explicit.

`paper comments upvote` toggles the authenticated upvote state for a comment. It prompts for
confirmation unless `--yes` is supplied.

`paper comments delete` deletes a comment by id. It prompts for confirmation unless `--yes` is
supplied.

`paper similar` calls the public similar-papers endpoint. Add `--limit <n>` to trim the returned
cards and `--raw` to print the raw JSON payload.

`paper text` calls the public full-text endpoint for the resolved paper version UUID.

- Without `--page`, it prints every page in order.
- `--page <n>` is repeatable and limits output to specific 1-based pages.

`paper pdf url` prints the resolved fetcher URL for the public PDF.

`paper pdf download` accepts either `<path>` or `<paper-id> <path>`. If the paper id is omitted,
it uses the current saved paper context.

`paper vote` toggles the authenticated vote state for the paper's group id. It prompts for
confirmation unless `--yes` is supplied.

`paper view` records an authenticated paper view against the paper's group id. It prompts for
confirmation unless `--yes` is supplied.

## Assistant

```bash
alphaxiv assistant list
alphaxiv assistant list --paper 1706.03762
alphaxiv assistant model
alphaxiv assistant url-metadata https://github.com/PKU-YuanGroup/Helios
alphaxiv assistant set-model "Claude 4.6 Sonnet"
alphaxiv assistant start "Find papers on agent frameworks"
alphaxiv assistant start --model "GPT 5.4" "Find papers on agent frameworks"
alphaxiv assistant reply "Focus on the most cited ones"
alphaxiv assistant history
```

The assistant uses authenticated `assistant/v2` endpoints and streams responses over
`text/event-stream`.

`assistant list` defaults to homepage chats. Add `--paper <paper-id>` to list paper-scoped chats
for a specific paper.

`assistant model` reads and prints the current preferred assistant model from `GET /users/v3`.

`assistant set-model <label-or-id>` persists the preferred assistant model through
`PATCH /users/v3/preferences`.

`assistant url-metadata <url>` fetches the assistant-side link preview metadata for a URL. Add
`--raw` to print the raw JSON payload.

The CLI does not claim to know the full live model catalog. It reads the current preferred model
from `GET /users/v3` and accepts explicit ids or label-like input without local catalog
validation.

`assistant start` options:

- `--paper <paper-id>` starts a paper-scoped chat
- `--model <label-or-id>` overrides the model for that request without changing the saved
  preference
- `--web-search off|full`
- `--thinking / --no-thinking`
- `--raw` prints raw SSE event payloads instead of the friendly renderer

`assistant reply` accepts either:

- `alphaxiv assistant reply "next question"` to use the saved current assistant chat
- `alphaxiv assistant reply <session-id> "next question"` to target a specific session

`assistant reply` also accepts `--model <label-or-id>` for a one-off model override.

`assistant history` accepts an optional session id. Without one, it uses the saved current
assistant chat.

This assistant surface is distinct from the public `search` commands:

- `search` calls public paper, topic, and organization search endpoints
- `assistant` calls the authenticated alphaXiv assistant and can invoke internal tools such as
  embedding similarity search and paper retrieval

## Folders

```bash
alphaxiv folders list
alphaxiv folders list --papers
```

`folders list` calls the authenticated folders endpoint and prints folder summaries. Add `--papers`
to include the papers in each folder, or `--raw` to print the raw JSON payload.
