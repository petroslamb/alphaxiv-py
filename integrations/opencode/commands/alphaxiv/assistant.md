---
description: Use the alphaXiv assistant after retrieval
---

Use the authenticated alphaXiv assistant after deterministic retrieval.

Recommended sequence:

1. Retrieve papers first with `search`, `feed`, or `paper`.
2. Start a new chat with `alphaxiv assistant start "<message>"`.
3. Add `--paper <paper-id>` when the new chat should be grounded in a specific paper.
4. Continue an existing chat with `alphaxiv assistant reply "<message>"`.
5. Inspect saved chats with `alphaxiv assistant list` and `alphaxiv assistant history`.

Do not use the assistant as the first-step replacement for `search` or `feed`.
