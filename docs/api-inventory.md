# API Inventory

Last verified: March 12, 2026

This is a confirmed inventory of alphaXiv endpoints observed from live traffic and direct probing. It is not an official contract, and alphaXiv does not appear to publish public API docs or an OpenAPI schema.

## Docs Discovery

These common documentation paths were probed on `https://api.alphaxiv.org` and returned `404`:

- `/openapi.json`
- `/swagger`
- `/swagger.json`
- `/api-json`
- `/docs`
- `/redoc`
- `/v3/api-docs`
- `/swagger-ui`
- `/reference`

`https://api.alphaxiv.org` itself returns HTML, not an API index.

## Base Hosts

- `https://api.alphaxiv.org`: primary JSON and SSE API
- `https://fetcher.alphaxiv.org`: PDF fetch URLs
- `https://paper-podcasts.alphaxiv.org`: podcast audio and transcript assets
- `https://clerk.alphaxiv.org`: Clerk auth endpoints used by the web app

## Confirmed Endpoints

`Used by alphaxiv-py` refers to the current implementation in this repository.

### Search and Discovery

| Method | Path | Access | Description | Used by alphaxiv-py |
| --- | --- | --- | --- | --- |
| `GET` | `/search/v2/paper/fast?q=...&includePrivate=false` | public | Fast paper search used by homepage search. | yes |
| `GET` | `/v1/search/closest-topic?input=...` | public | Topic suggestion endpoint used by homepage search. | yes |
| `GET` | `/organizations/v2/search?q=...` | public | Organization search for labs, universities, and companies. | yes |
| `GET` | `/organizations/v2/top` | public | Top organizations list used by homepage filtering UI. | yes |

### Papers

| Method | Path | Access | Description | Used by alphaxiv-py |
| --- | --- | --- | --- | --- |
| `GET` | `/papers/v3/legacy/{canonical_or_versioned_id}` | public | Main paper metadata payload for canonical or versioned arXiv IDs. | yes |
| `GET` | `/papers/v3/legacy/{bare_id}` | public | Direct legacy lookup by bare arXiv ID. | yes |
| `GET` | `/papers/v3/legacy/{paperGroupId}/comments` | public | Public paper comments thread. | yes |
| `POST` | `/papers/v2/{paperVersionId}/comment` | auth write | Creates a top-level paper comment or a reply when `parentCommentId` is set. | yes |
| `GET` | `/papers/v3/{paperVersionId}/full-text` | public | Page-level extracted paper text. | yes |
| `GET` | `/papers/v3/{paperVersionId}/overview/{lang}` | public | AI overview or blog payload for a paper version. | yes |
| `GET` | `/papers/v3/{paperVersionId}/overview/status` | public | Overview generation and translation status. | yes |
| `GET` | `/papers/v3/x-mentions-db/{paperGroupId}` | public | Social mentions and related resource metadata. | yes |
| `POST` | `/papers/v3/{paperGroupId}/view` | public write | Records a paper view. | yes |
| `GET` | `/papers/v3/{paperId}/similar-papers` | public | Similar-papers list shown in the paper UI. | yes |

### Assistant

| Method | Path | Access | Description | Used by alphaxiv-py |
| --- | --- | --- | --- | --- |
| `GET` | `/assistant/v2?variant=homepage` | auth | Lists homepage assistant sessions. | yes |
| `GET` | `/assistant/v2?variant=paper&paperVersion={paperVersionId}` | auth | Lists paper-scoped assistant sessions. | yes |
| `GET` | `/assistant/v2/{sessionId}/messages` | auth | Returns structured assistant message history. | yes |
| `POST` | `/assistant/v2/chat` | auth | Starts or continues an assistant chat and returns SSE output. | yes |
| `GET` | `/assistant/v2/url-metadata?url=...` | auth | Fetches link metadata used in assistant or comment rendering. | yes |

### User and Preferences

| Method | Path | Access | Description | Used by alphaxiv-py |
| --- | --- | --- | --- | --- |
| `GET` | `/users/v3` | auth | Current user profile and preferences. | yes |
| `PATCH` | `/users/v3/preferences` | auth write | Updates user preferences such as preferred assistant model. | yes |
| `GET` | `/folders/v3` | auth | Returns user folders or bookmark containers. | yes |

### Voting and Social Actions

| Method | Path | Access | Description | Used by alphaxiv-py |
| --- | --- | --- | --- | --- |
| `POST` | `/v2/papers/{paperId}/vote` | auth write | Toggles a paper like or vote. | yes |
| `POST` | `/comments/v2/{commentId}/upvote` | auth write | Toggles a comment upvote. | yes |
| `DELETE` | `/comments/v2/{commentId}` | auth write | Deletes a comment by id. | yes |

## Related Non-API Asset Endpoints

These are not under `api.alphaxiv.org`, but they are part of the product surface and are useful for clients.

| Method | URL Pattern | Description | Used by alphaxiv-py |
| --- | --- | --- | --- |
| `GET` | `https://fetcher.alphaxiv.org/v2/pdf/{canonical_id}.pdf` | PDF download URL used by the paper UI. | yes |
| `GET` | `https://paper-podcasts.alphaxiv.org/{paperGroupId}/podcast.mp3` | Podcast audio for a paper. | yes |
| `GET` | `https://paper-podcasts.alphaxiv.org/{paperGroupId}/transcript.json` | Podcast transcript JSON. | yes |
| `GET` | `https://clerk.alphaxiv.org/v1/environment` | Clerk environment bootstrap. | no |
| `GET` | `https://clerk.alphaxiv.org/v1/client` | Clerk client bootstrap. | no |

## Routes Currently Used By This Repository

These are the endpoint groups currently wired into the SDK and CLI:

- Search: `/search/v2/paper/fast`, `/v1/search/closest-topic`, `/organizations/v2/search`
- Feed support: `/organizations/v2/top`
- Papers: `/papers/v3/legacy/{id}`, `/papers/v3/legacy/{paperGroupId}/comments`, `/papers/v2/{paperVersionId}/comment`, `/papers/v3/{paperVersionId}/full-text`, `/papers/v3/{paperVersionId}/overview/{lang}`, `/papers/v3/{paperVersionId}/overview/status`, `/papers/v3/x-mentions-db/{paperGroupId}`, `/papers/v3/{paperGroupId}/view`, `/papers/v3/{paperId}/similar-papers`, `/v2/papers/{paperId}/vote`
- Assistant: `/assistant/v2?variant=homepage`, `/assistant/v2?variant=paper&paperVersion=...`, `/assistant/v2/{sessionId}/messages`, `/assistant/v2/chat`, `/assistant/v2/url-metadata`
- Auth and preferences: `/users/v3`, `/users/v3/preferences`, `/folders/v3`, `/comments/v2/{commentId}/upvote`, `/comments/v2/{commentId}`
- Related hosts: `fetcher.alphaxiv.org` PDF URLs and `paper-podcasts.alphaxiv.org` transcript or podcast assets

## Notes

- The homepage paper feed is largely server-rendered on `www.alphaxiv.org`, with API support from endpoints like `/organizations/v2/top`.
- `PATCH /users/v3/preferences` appears broader than model selection alone; the web UI uses it for other assistant-pane preferences too.
- `/papers/v3/{paperId}/similar-papers` returns noisy variants for some papers, including malformed or duplicate IDs. Any client support should canonicalize those results before surfacing them.
- `POST /papers/v2/{paperVersionId}/comment` supports both top-level comments and replies. The web payload also contains annotation fields, but the current SDK/CLI intentionally expose only text fields in v1.
- Multiple plausible comment edit routes were probed live and returned `404`; comment editing is not currently confirmed.
- This inventory is based on live observation, not on official vendor documentation.
