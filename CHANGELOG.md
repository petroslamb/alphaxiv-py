# Changelog

All notable changes to this project will be documented in this file.

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
