# CLI Reference

The CLI is organized around resource groups:

- `alphaxiv auth`
- `alphaxiv context`
- `alphaxiv search`
- `alphaxiv feed`
- `alphaxiv paper`
- `alphaxiv assistant`
- `alphaxiv folders`
- `alphaxiv guide`
- `alphaxiv skill`
- `alphaxiv agent`

For automation and agent use:

- `--json` is the stable machine-readable output mode
- `--raw` is the backend-shaped payload/debug mode on commands that already expose it
- commands that support both reject `--raw --json`

## Auth

```bash
alphaxiv auth set-api-key --api-key "$ALPHAXIV_API_KEY"
alphaxiv auth login-web
alphaxiv auth status
alphaxiv auth clear
alphaxiv auth clear-web
```

`auth set-api-key --api-key <key>` validates and saves an explicit alphaXiv API key to
`api-key.json`.

`auth set-api-key` without `--api-key` prompts for the API key with hidden input before
validating and saving it.

`auth login-web` opens a persistent Chromium profile under `ALPHAXIV_HOME/browser-profile`,
waits for you to complete the alphaXiv sign-in flow, and saves the resulting browser-backed auth
to `auth.json`.

Browser support is optional. Install it only if you need `auth login-web`:

```bash
uv sync --extra browser
uv run playwright install chromium
```

Or from PyPI:

```bash
pip install "alphaxiv-py[browser]"
playwright install chromium
```

Treat `auth login-web` as one-time setup for a persistent browser profile. After it succeeds, use
`alphaxiv assistant ...` normally; the CLI will try to refresh the saved web token automatically
from `ALPHAXIV_HOME/browser-profile`.

If a user keeps rerunning `auth login-web`, check these first:

- `ALPHAXIV_HOME` changes between runs
- the environment is ephemeral and does not preserve `~/.alphaxiv`
- `browser-profile` is being deleted or recreated
- the underlying alphaXiv web session was signed out

In normal use, rerun `auth login-web` only when the real web session is gone or the user moved to
a new machine or container.

`auth status` prints both the API-key state and the saved browser-backed auth state.

`auth clear` removes the locally saved `api-key.json`.

`auth clear-web` removes the locally saved `auth.json`. Add `--clear-browser-profile` if you also
want to delete the persistent Playwright profile.

## Context

```bash
alphaxiv context show
alphaxiv context show --json
alphaxiv context show paper
alphaxiv context show assistant
alphaxiv context use paper 1706.03762
alphaxiv context use assistant <session-id>
alphaxiv context clear
alphaxiv context clear paper
alphaxiv context clear assistant
```

`context show` prints both the current paper context and current assistant context. Add `--json`
for a stable object with `paper` and `assistant` keys.

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
alphaxiv search papers "attention is all you need" --json
alphaxiv search organizations "attention is all you need"
alphaxiv search topics "attention is all you need"
```

`search all` performs the homepage-style search and prints paper matches plus suggested topics and
organization matches when available. Add `--json` for a normalized result object.

`search papers` calls only the public paper search endpoint. Add `--json` for a stable list of
normalized paper matches.

`search organizations` calls only the public organization search endpoint. Add `--json` for
normalized organization objects.

`search topics` calls only the public closest-topic endpoint. Add `--json` for a normalized topic
list.

## Feed

```bash
alphaxiv feed filters
alphaxiv feed filters --json
alphaxiv feed filters search "agentic"
alphaxiv feed filters search "agentic" --json
alphaxiv feed list --sort hot --limit 10
alphaxiv feed list --sort hot --limit 10 --json
alphaxiv feed list --sort likes --limit 5
alphaxiv feed list --organization MIT --source twitter --interval 30-days --limit 5
alphaxiv feed list --category computer-science --custom-category generative-models --limit 5
alphaxiv feed list --topic agentic-frameworks --organization Meta --limit 5
alphaxiv feed list --source github --sort most-stars --limit 5
```

`feed filters` prints the current feed filter groups. Add `--json` for a normalized object with
sorts, intervals, sources, and organizations.

`feed filters search` mirrors the website filter drawer search box by querying live topic and
organization filters. Add `--json` to return normalized topic and organization results.

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

`feed list --json` returns the selected filters plus normalized feed cards.

## Paper

```bash
alphaxiv paper show 1706.03762
alphaxiv paper show 1706.03762 --json
alphaxiv paper abstract 1706.03762
alphaxiv paper summary 1706.03762
alphaxiv paper summary 1706.03762 --json
alphaxiv paper overview 1706.03762
alphaxiv paper overview 1706.03762 --json
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

These read commands support `--json`:

- `paper show`
- `paper abstract`
- `paper summary`
- `paper overview`
- `paper overview-status`
- `paper resources`
- `paper text`
- `paper similar`
- `paper comments list`
- `paper folders list`
- `paper pdf url`

`paper abstract` prints the paper title and abstract from the main paper metadata payload. Add
`--json` for a stable object with the title, abstract, and resolved ids.

`paper summary` prints the structured AI summary from the overview endpoint. Add
`--language <code>` to request a translated summary, `--json` for normalized structured output, or
`--raw` to print the raw structured summary payload.

`paper overview --machine` prints only the raw machine-readable markdown shown behind the overview
page's `Machine` toggle. Use `--json` for a normalized object with summary, overview markdown, and
citations. `--machine` and `--json` are mutually exclusive.

`paper overview-status` calls the public overview status endpoint and prints the generation state
plus available translation languages.

`paper resources --bibtex` prints the paper's BibTeX citation when alphaXiv exposes one. Add
`--json` to return a normalized `bibtex` object instead of plain text.

`paper resources --transcript` prints the AI audio summary transcript when the paper has a public
podcast transcript. Add `--json` for normalized transcript lines and joined transcript text.

`paper comments list` calls the public comments endpoint and renders the nested thread. Add `--raw`
to print the raw JSON payload or `--json` for normalized nested comments.

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
cards, `--json` for normalized similar-card output, or `--raw` to print the raw JSON payload.

`paper text` calls the public full-text endpoint for the resolved paper version UUID.

- Without `--page`, it prints every page in order.
- `--page <n>` is repeatable and limits output to specific 1-based pages.
- Add `--json` for normalized page objects and joined text.

`paper pdf url` prints the resolved fetcher URL for the public PDF. Add `--json` for a stable
`paper_id` + `pdf_url` object.

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
alphaxiv assistant list --json
alphaxiv assistant model
alphaxiv assistant model --json
alphaxiv assistant url-metadata https://github.com/PKU-YuanGroup/Helios
alphaxiv assistant set-model "Claude 4.6 Sonnet"
alphaxiv assistant start "Find papers on agent frameworks"
alphaxiv assistant start --model "GPT 5.4" "Find papers on agent frameworks"
alphaxiv assistant reply "Focus on the most cited ones"
alphaxiv assistant history
alphaxiv assistant history --json
```

The assistant uses authenticated `assistant/v2` endpoints and streams responses over
`text/event-stream`.

Assistant commands prefer the saved web login from `alphaxiv auth login-web` when it is available,
and otherwise fall back to API-key auth.

`assistant list` defaults to homepage chats. Add `--paper <paper-id>` to list paper-scoped chats
for a specific paper. Add `--json` for a normalized session list.

`assistant model` reads and prints the current preferred assistant model from `GET /users/v3`.
Add `--json` for a normalized `{"model": ...}` object.

`assistant set-model <label-or-id>` persists the preferred assistant model through
`PATCH /users/v3/preferences`.

`assistant url-metadata <url>` fetches the assistant-side link preview metadata for a URL. Add
`--json` for normalized metadata or `--raw` to print the raw JSON payload.

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
assistant chat. Add `--json` for normalized message objects or `--raw` for backend payloads.

`assistant reply` continues the same saved remote session. Very long chats can become slower to
answer over time. If latency starts climbing and you no longer need the whole prior thread active,
start a fresh session with `assistant start` and restate only the context you still need. Keep the
older chat for reference with `assistant history` or `assistant list`. This is the mitigation the
CLI can offer when the slowdown is coming from accumulated chat state.

This assistant surface is distinct from the public `search` commands:

- `search` calls public paper, topic, and organization search endpoints
- `assistant` calls the authenticated alphaXiv assistant and can invoke internal tools such as
  embedding similarity search and paper retrieval

## Folders

```bash
alphaxiv folders list
alphaxiv folders list --papers
alphaxiv folders list --json
alphaxiv folders show "Want to read"
alphaxiv folders show "Want to read" --json
```

`folders list` calls the authenticated folders endpoint and prints folder summaries. Add `--papers`
to include the papers in each folder, `--json` for normalized folder objects, or `--raw` to print
the raw JSON payload.

`folders show <folder>` prints one folder with its full paper list. Add `--json` for normalized
folder output or `--raw` to print the raw JSON payload.

## Guide

```bash
alphaxiv guide
alphaxiv guide research
alphaxiv guide paper
alphaxiv guide assistant
alphaxiv guide feed
```

`guide` is workflow-only. It does not repeat the command reference. Use it when `--help` is not
enough and you want a task-level sequence such as recent-paper discovery or paper inspection.

## Skill

```bash
alphaxiv skill install
alphaxiv skill install --scope project --target codex
alphaxiv skill status --scope all
alphaxiv skill status --scope all --json
alphaxiv skill show --target source
alphaxiv skill show --target opencode
alphaxiv skill uninstall --target claude-code --yes
```

`skill install` copies packaged alphaXiv integrations into user-level or project-level agent
directories for Codex, Claude Code, and OpenCode.

`skill status` inspects installed targets. Add `--json` for normalized installation records.

`skill show --target source` prints the canonical packaged Codex `SKILL.md` source. Other targets
print the packaged install bundle for that target.

`skill uninstall` removes only installs that were managed by `alphaxiv skill install`. It refuses
to delete unmanaged repository/source files.

## Agent

```bash
alphaxiv agent show codex
alphaxiv agent show claude-code
alphaxiv agent show opencode
```

`agent show <target>` prints the target-specific integration guidance, install paths, and included
files for Codex, Claude Code, or OpenCode.
