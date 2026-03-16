---
description: Use alphaXiv feed filters and rankings correctly
---

Use `feed` when the user wants recent or ranked discovery instead of direct keyword lookup.

Key distinctions:

- `alphaxiv search ...` is keyword search.
- `alphaxiv feed filters search "<query>"` finds accepted topic and organization filter values.
- `alphaxiv feed list ...` pulls the ranked homepage feed.

Ranking guidance:

- `--sort hot` for homepage prominence
- `--sort likes` for engagement
- `--source github --sort most-stars` for implementation traction

Do not invent `--topic` values. Discover them with `feed filters search` first.
