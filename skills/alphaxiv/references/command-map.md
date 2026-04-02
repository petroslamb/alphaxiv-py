# alphaXiv CLI command map

## Command-family summary

| Command family | Use it for | Auth required | Saved paper context | Mutates state |
| --- | --- | --- | --- | --- |
| `search all|papers|topics|organizations` | Keyword-driven lookup of papers, topics, and organizations | No | No | No |
| `feed filters|list` | Discover topic slugs and rank recent papers from the homepage feed | No | No | No |
| `paper show|abstract|summary|overview|overview-status|resources|text|similar|pdf url|pdf download|comments list` | Inspect one paper and read public paper data | No | Yes | No |
| `paper vote|view` | Record paper-level engagement | Yes | Yes | Yes |
| `paper comments add|reply|upvote|delete` | Authenticated comment actions on a paper thread | Yes | `add` and `reply` can use saved paper context; `upvote` and `delete` need a comment id | Yes |
| `paper folders list|add|remove` | Inspect or change which of your folders contain one paper | Yes | Yes | `list` no, `add` and `remove` yes |
| `assistant list|history|model|set-model|start|reply|url-metadata` | Assistant chats, assistant settings, and link metadata | Yes, via API key or saved web login | `reply` can use saved assistant context; `start` needs explicit `--paper` for paper grounding | `start`, `reply`, and `set-model` change remote state; very long `reply` chains may get slower |
| `folders list|show` | Inspect all authenticated folders and the papers inside them | Yes | No | No |
| `context show|use|clear` | Manage the locally saved current paper and assistant session | No | n/a | Local state only |
| `auth set-api-key|login-web|status|clear|clear-web` | Manage the locally saved API key and optional browser-backed auth | No saved key required | n/a | Local state; `set-api-key` and `login-web` also validate remotely |

## Nearby-command disambiguation

| If the user wants... | Use this command | Why |
| --- | --- | --- |
| Keyword matches for a phrase or idea | `alphaxiv search papers "<query>"` | `search` is keyword-driven, not feed-ranked |
| Recent or ranked papers on a topic | `alphaxiv feed filters search "<topic>"` then `alphaxiv feed list ...` | `feed` is the discovery surface for recent and ranked papers |
| The author-written abstract | `alphaxiv paper abstract <paper-id>` | `paper summary` and `paper overview` are AI-generated |
| A quick AI digest | `alphaxiv paper summary <paper-id>` | Shorter than `paper overview`, more synthetic than `paper abstract` |
| A longer generated explanation | `alphaxiv paper overview <paper-id>` | Use when the short summary is not enough |
| Readable paper body text | `alphaxiv paper text <paper-id>` | This is extracted text, not the original PDF file |
| The actual PDF file | `alphaxiv paper pdf download <paper-id> ./paper.pdf` | Use this when the output should be a saved file |
| A new assistant conversation | `alphaxiv assistant start "..."` | `assistant reply` continues an existing saved session; switch back to `start` if a long thread gets slow |
| Continue the current assistant chat | `alphaxiv assistant reply "..."` | Use after `assistant start` or `context use assistant ...`; it keeps growing the same remote session |
| Save a paper for repeated use | `alphaxiv context use paper <paper-id>` | Lets many later `paper` commands omit the id |
| Check which folders already contain a paper | `alphaxiv paper folders list <paper-id>` | `folders list` shows all folders, not one paper's membership |

## Agent rules of thumb

- Prefer `search`, `feed`, and `paper` before `assistant`.
- Use `feed` when importance, recency, or ranking matters; use `search` when keywords are already known.
- Use `paper text` when the user asks for the full text or readable paper body.
- Use `paper pdf download` when the user wants the file itself.
- If a long assistant chat becomes slow, prefer a fresh `assistant start` with a concise recap over
  continuing the same session indefinitely.
- Avoid mutating commands unless the user explicitly asks to change remote state.
