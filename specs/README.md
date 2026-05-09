# alphaXiv-py Specs

This directory is the source of truth for accepted behavior in `alphaxiv-py`.
Implementation PRs must update the matching feature spec before or alongside any
SDK or CLI behavior change.

Phase 0 creates the scaffold and checker only. It does not change SDK or CLI
behavior.

## Feature Specs

| Spec | Status | Surface |
| --- | --- | --- |
| [Search, discovery, and feed](features/search-discovery-feed.md) | Implemented | Public search, topic, organization, and feed endpoints |
| [Paper reads and resources](features/paper-reads-and-resources.md) | Implemented | Public paper metadata, text, overview, comments, resources, and related assets |
| [Paper AI detection and model links](features/paper-ai-detection-and-model-links.md) | Implemented | Public paper AI-detection and model-link sidecar endpoints |
| [Authenticated assistant](features/authenticated-assistant.md) | Implemented | Authenticated assistant sessions, messages, chat, model preference, and URL metadata |
| [Auth, folders, and social actions](features/auth-folders-social-actions.md) | Implemented | Auth setup, current user, folders, votes, comments, and preferences |
| [CLI guides and agent integrations](features/cli-guides-and-agent-integrations.md) | Implemented | Workflow guides, packaged skills, and Codex, Claude Code, and OpenCode integration installs |
| [Paper preview, slug resolution, and figures](features/paper-preview-slug-resolution-and-figures.md) | Implemented | Public paper preview, alphaXiv direct resolution fallback, and paper figures |
| [Events and rich paper search](features/events-and-rich-paper-search.md) | Implemented | Public events list and richer public paper search endpoints |
| [Public read expansion](features/public-read-expansion.md) | Proposed | Future confirmed public read endpoints |
| [Authenticated expansion backlog](features/authenticated-expansion-backlog.md) | Backlog | Future authenticated assistant usage, context-window, people, organization, and profile surfaces |

## Required Feature Spec Sections

Every file under `specs/features/` must include:

- `## Status`
- `## Endpoint Evidence`
- `## Acceptance Criteria`
- `## Validation Commands`

Run the checker before handoff:

```bash
uv run python scripts/check_specs.py
```

Focused checker tests:

```bash
uv run pytest tests/unit/test_check_specs.py -q
```
