# alphaXiv CLI workflows

These are higher-level task workflows. They are not a second command reference.

## Find important recent papers on a topic

Goal:

- Find recent papers on a topic and rank candidates using alphaXiv's feed signals.

Recommended command order:

```bash
alphaxiv feed filters search "multi-agent systems"
alphaxiv feed list --interval 90-days --topic <topic-slug> --sort hot --limit 10
alphaxiv feed list --interval 90-days --topic <topic-slug> --sort likes --limit 10
alphaxiv feed list --interval 90-days --source github --topic <topic-slug> --sort most-stars --limit 10
alphaxiv paper summary <paper-id>
```

How to interpret the outputs:

- `feed filters search` returns the actual topic slugs accepted by the feed.
- `feed list` is the best surface for recent-paper discovery and rough importance ranking.
- `paper summary` is the fastest way to validate whether a candidate is actually on-topic before deeper reading.

Common mistakes:

- Using `search papers` when the real need is recent or ranked discovery.
- Guessing topic slugs instead of discovering them with `feed filters search`.
- Jumping into `assistant` before you have candidate paper ids.

## Get the readable paper text or the PDF

Goal:

- Get either the extracted paper body as text or the original PDF file.

Recommended command order:

```bash
alphaxiv context use paper <paper-id>
alphaxiv paper text
alphaxiv paper text --page 1 --page 2
alphaxiv paper pdf url
alphaxiv paper pdf download ./paper.pdf
```

How to interpret the outputs:

- `paper text` returns readable text extracted from the PDF.
- `paper pdf url` prints the resolved public PDF URL.
- `paper pdf download` saves the original file locally.

Common mistakes:

- Using `paper pdf download` when the user actually wants readable text.
- Using `paper summary` when the task requires the paper body itself.

## Inspect one paper deeply

Goal:

- Understand what one paper is, what it claims, and what related resources exist.

Recommended command order:

```bash
alphaxiv context use paper <paper-id>
alphaxiv paper show
alphaxiv paper abstract
alphaxiv paper summary
alphaxiv paper overview
alphaxiv paper resources
alphaxiv paper similar --limit 5
```

How to interpret the outputs:

- `paper show` confirms the ids, links, authors, and topics.
- `paper abstract` gives the author-written abstract.
- `paper summary` is the short AI digest.
- `paper overview` is the long AI write-up when the summary is not enough.
- `paper resources` surfaces BibTeX, transcript, links, and implementations.
- `paper similar` is the best next step for adjacent papers.

Common mistakes:

- Confusing `abstract`, `summary`, and `overview`.
- Skipping `paper show` when the paper id or resolved identity is still uncertain.

## Build and refine a shortlist

Goal:

- Turn a rough set of candidates into a smaller, better-justified shortlist.

Recommended command order:

```bash
alphaxiv search papers "<keywords>"
alphaxiv paper summary <paper-id>
alphaxiv paper similar <paper-id> --limit 5
alphaxiv paper resources <paper-id>
alphaxiv context use paper <paper-id>
alphaxiv paper overview
```

How to interpret the outputs:

- `search papers` works best when you already have a phrase or idea in mind.
- `paper similar` expands one promising paper into a local neighborhood of related work.
- `paper resources` is useful when code, implementations, or transcript artifacts affect the shortlist.
- `paper overview` helps decide whether a paper belongs in the final cut.

Common mistakes:

- Using only one signal or one query and never expanding with `paper similar`.
- Treating `assistant` as the first-pass retrieval surface instead of using `search`, `feed`, and `paper` first.

## Use the assistant after retrieval

Goal:

- Use the authenticated assistant for comparison, synthesis, and follow-up after you already have paper ids or a specific paper in mind.

Auth setup note:

- If assistant chat writes are restricted for the API key, run `alphaxiv auth login-web` once and keep `ALPHAXIV_HOME` and `browser-profile` stable. Do not rerun it before every assistant command.

Recommended command order:

```bash
alphaxiv assistant start "Find the main contribution and weakness of this paper" --paper <paper-id>
alphaxiv assistant reply "Compare it with the previous two papers we discussed"
alphaxiv assistant history
alphaxiv assistant list --paper <paper-id>
```

How to interpret the outputs:

- `assistant start` begins a new assistant chat and saves it as the current session.
- `assistant reply` continues the current or selected session.
- `assistant history` is the transcript view for the saved session.
- `assistant list --paper` is the best way to inspect the saved chats that belong to one paper.

Common mistakes:

- Assuming `assistant start` automatically uses saved paper context. It does not; use `--paper <paper-id>` when you want paper grounding in a new chat.
- Using `assistant` as the first-step discovery mechanism when `search`, `feed`, or `paper` would be more deterministic.
- Repeating `auth login-web` on every use instead of keeping the persistent browser profile.

## Work with folders and comments when authenticated

Goal:

- Save papers into folders, inspect folder contents, and participate in paper comment threads.

Recommended command order:

```bash
alphaxiv auth set-api-key --api-key "$ALPHAXIV_API_KEY"
alphaxiv folders list
alphaxiv paper folders list <paper-id>
alphaxiv paper folders add <paper-id> "Want to read"
alphaxiv paper comments list <paper-id>
alphaxiv paper comments add <paper-id> --body "Helpful note"
alphaxiv paper comments reply <paper-id> <comment-id> --body "Thanks"
```

How to interpret the outputs:

- `folders list` shows the user's authenticated folder set.
- `paper folders list` shows which of those folders already contain the selected paper.
- `paper comments list` is public read access for the thread.
- `paper comments add` and `reply` are authenticated mutations.

Common mistakes:

- Forgetting that `folders` and comment mutations require an API key.
- Using `paper comments delete` or `upvote` without an actual comment id.
