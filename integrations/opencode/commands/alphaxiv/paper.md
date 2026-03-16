---
description: Inspect one paper with the alphaXiv CLI
---

Choose the command based on what the user actually needs:

- `alphaxiv paper show <paper-id>` for ids, authors, topics, and links
- `alphaxiv paper abstract <paper-id>` for the original abstract
- `alphaxiv paper summary <paper-id>` for the short AI digest
- `alphaxiv paper overview <paper-id>` for the long AI write-up
- `alphaxiv paper text <paper-id>` for readable text extracted from the PDF
- `alphaxiv paper pdf download <paper-id> ./paper.pdf` for the original PDF file
- `alphaxiv paper resources <paper-id>` for citations, transcripts, mentions, and implementations

If multiple commands target the same paper, run `alphaxiv context use paper <paper-id>` first.
