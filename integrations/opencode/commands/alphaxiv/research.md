---
description: Find recent important papers with the alphaXiv CLI
---

Use the `alphaxiv` CLI to discover and shortlist papers.

Workflow:

1. Use `alphaxiv feed filters search "<topic>"` to discover accepted topic slugs.
2. Use `alphaxiv search papers "<topic>"` when the user already has keyword terms.
3. Use `alphaxiv feed list --interval 90-days --sort hot --topic <slug>` to find recent important candidates.
4. Compare `--sort hot`, `--sort likes`, and `--source github --sort most-stars` when importance is fuzzy.
5. Inspect the shortlist with `alphaxiv paper show`, `paper summary`, and `paper resources`.

Prefer deterministic retrieval before the assistant.
