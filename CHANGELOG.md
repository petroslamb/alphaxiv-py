# Changelog

All notable changes to this project will be documented in this file.

## 0.4.2 - 2026-04-02

- Documented that long-running assistant chat sessions can slow down over time
  because `assistant reply` keeps extending the same remote session.
- Added the current CLI mitigation: start a fresh chat with `assistant start`
  and carry forward only the minimal recap or paper ids you still need, while
  keeping the older session available through `assistant history` or
  `assistant list`.
- Updated the in-CLI assistant guide text and the shipped alphaXiv skill so
  users and agents both surface the same long-session warning and mitigation.

## 0.4.1 - 2026-04-02

- Clarified the browser-backed auth operating model in the README and CLI
  reference, including that `alphaxiv auth login-web` is one-time setup tied to
  a persistent `ALPHAXIV_HOME` and browser profile.
- Updated the shipped alphaXiv skill and reference files so assistant auth
  guidance reflects the restored web-login path instead of describing assistant
  commands as API-key-only.
- Synced the lockfile package version to `0.4.1`.

## 0.4.0 - 2026-04-02

- Restored optional browser-backed auth through `alphaxiv auth login-web`,
  `alphaxiv auth clear-web`, and saved `auth.json` / browser-profile support.
- Updated assistant commands to prefer the saved web login when it is
  available, while keeping API-key auth for the rest of the authenticated CLI
  surface.
- Added SDK support for explicit bearer auth plus
  `AlphaXivClient.from_saved_browser_auth()` and
  `AlphaXivClient.from_saved_auth(prefer_browser=True)`.
- Expanded unit, integration, and live smoke coverage for the restored browser
  auth flow, including assistant write smoke that can seed browser-backed auth
  from the operator's real alphaXiv session when available.
- Restored the optional `browser` dependency extra for Playwright-backed auth
  flows and documented the new assistant auth behavior in the CLI and Python
  docs.

## 0.3.0 - 2026-03-17

- Added NotebookLM-style agent UX improvements with built-in `guide`, `skill`,
  and `agent` command groups.
- Added stable `--json` output across the main read and discovery commands for
  agent-safe structured output, while keeping `--raw` as the backend-shaped
  debug surface.
- Added packaged runtime assets and install/status/show/uninstall flows for
  Codex, Claude Code, and OpenCode integrations.
- Added representative live JSON smoke coverage for `feed`, `assistant`, and
  `folders` reads, plus unit coverage for the new guide, skill, and JSON
  surfaces.

## 0.2.0 - 2026-03-16

- Reorganized the CLI around resource-first groups such as `auth`, `context`,
  `search`, `feed`, `paper`, `assistant`, and `folders`.
- Expanded the paper surface with abstract, summary, overview, PDF, full-text,
  comments, similar-paper, and paper-folder workflows under `alphaxiv paper`.
- Added authenticated comment create, reply, delete, and upvote support plus
  authenticated paper-folder membership management.
- Added folder membership CLI coverage and live smoke coverage for feed and
  folder flows.
- Improved CLI discoverability with richer help text, suggestion-oriented error
  messages, and nearest-command guidance for agent and terminal use.
- Added a repo-shipped optional Codex skill for alphaXiv CLI research
  workflows.

## 0.1.0 - 2026-03-13

Initial public release.

- Added an API-key-only SDK and CLI for alphaXiv.
- Implemented public search, feed, paper metadata, overview, transcript, PDF, comments, and similar-paper endpoints.
- Implemented authenticated assistant, folder, paper-vote, and comment-mutation flows.
- Added live smoke coverage for public feed, paper reads, assistant reads, folders, and reversible authenticated mutations.
