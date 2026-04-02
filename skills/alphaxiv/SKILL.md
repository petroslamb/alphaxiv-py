---
name: alphaxiv
description: Use when the user wants to work with the alphaXiv CLI to search for papers, inspect paper metadata or full text, manage saved paper or assistant context, or use the authenticated assistant, folders, or comments in terminal-based research workflows.
metadata:
  short-description: Use the alphaXiv CLI for research workflows
---

# alphaXiv CLI

Use this skill when the user wants to use the alphaXiv CLI to find papers, inspect one paper, build a shortlist, or use the authenticated assistant from the terminal.

This skill is CLI-only. Do not switch to Python SDK guidance unless the user explicitly asks for Python usage instead of terminal usage.

## Mental model

- `search`: keyword lookup when the user already has terms in mind and wants matching papers, topic suggestions, or organizations.
- `feed`: recent or ranked discovery from the public alphaXiv homepage feed. Use this for questions like "important recent papers" or when the user needs topic slugs before filtering.
- `paper`: inspect one paper. This is where to get metadata, the original abstract, AI summary, long overview, extracted paper text, PDF access, similar papers, comments, and paper-specific folder membership.
- `assistant`: authenticated synthesis after deterministic retrieval. Use this to explain, compare, or continue a research chat after `search`, `feed`, or `paper`.
- `context`: save or inspect the current paper or assistant session so later commands can omit ids.
- `auth`: manage API-key auth and optional browser-backed web login for assistant commands.

## Highest-confusion distinctions

- `search` vs `feed`: use `search` for keyword-driven lookup; use `feed` for recent or ranked discovery and for topic-filter workflows.
- `paper abstract`: the author-written abstract.
- `paper summary`: the short AI digest.
- `paper overview`: the longer AI write-up.
- `paper text`: readable text extracted from the PDF.
- `paper pdf download`: the actual PDF file saved locally.
- `assistant start` vs `assistant reply`: `start` opens a new assistant chat; `reply` continues the current or selected saved session.

## Auth rules

Public flows:

- `search`
- `feed`
- most read-only `paper` commands such as `show`, `abstract`, `summary`, `overview`, `overview-status`, `resources`, `text`, `similar`, `pdf`, and `comments list`
- `context`

API-key-authenticated flows:

- `folders`
- `paper vote`
- `paper view`
- `paper folders`
- `paper comments add`
- `paper comments reply`
- `paper comments upvote`
- `paper comments delete`

Assistant-authenticated flows:

- all `assistant` commands

Assistant commands can authenticate through either:

- `alphaxiv auth set-api-key`
- `alphaxiv auth login-web`

Prefer `auth login-web` when assistant chat writes are restricted for the API key. Treat
`auth login-web` as one-time setup for a persistent browser profile, not something to rerun before
every assistant command.

## Working rules

1. Prefer deterministic retrieval first: `search`, `feed`, and `paper`.
2. Use `assistant` after retrieval when the task becomes comparison, synthesis, or follow-up reasoning.
3. Use `context use paper <paper-id>` when several paper commands will target the same paper.
4. Do not run mutating commands unless the user explicitly wants to change state.
5. If a new assistant chat should be grounded in one paper, pass `--paper <paper-id>` to `assistant start`. A saved current paper does not automatically ground a new assistant chat.

## Reference map

Read only the reference file you need:

- `references/workflows.md`: task workflows that combine commands into research tasks.
- `references/command-map.md`: concise command-family map, auth requirements, mutation notes, and nearby-command disambiguation.
