# Python API

## Client

```python
from alphaxiv import AlphaXivClient
```

Use `AlphaXivClient` as an async context manager.

Recommended authenticated usage is an explicit API key:

```python
async with AlphaXivClient(api_key="axv1_...") as client:
    results = await client.search.papers("attention is all you need")
```

`AlphaXivClient.from_saved_api_key()` loads `ALPHAXIV_API_KEY` first and then falls back to the saved local API key from `alphaxiv auth set-api-key`.

## Search

```python
async with AlphaXivClient() as client:
    results = await client.search.papers("attention is all you need")
```

Individual public search endpoints:

```python
async with AlphaXivClient() as client:
    papers = await client.search.papers("reinforcement learning")
    organizations = await client.search.organizations("reinforcement learning")
    topics = await client.search.closest_topics("reinforcement learning")
```

Homepage-style search suggestions:

```python
async with AlphaXivClient() as client:
    results = await client.search.homepage("reinforcement learning")
    print(results.topics)
    print([item.name for item in results.organizations])
```

## Explore Feed

```python
async with AlphaXivClient() as client:
    options = await client.explore.filter_options()
    search = await client.explore.search_filters("agentic")
    cards = await client.explore.feed(
        sort="most-stars",
        organizations=("MIT",),
        topics=("agentic-frameworks",),
        source="GitHub",
        limit=5,
    )
```

## Papers

```python
async with AlphaXivClient() as client:
    resolved = await client.papers.resolve("1706.03762")
    paper = await client.papers.get("1706.03762")
    comments = await client.papers.comments("1706.03762")
    full_text = await client.papers.full_text("1706.03762")
    overview = await client.papers.overview("1706.03762")
    overview_status = await client.papers.overview_status("1706.03762")
    mentions = await client.papers.mentions("1706.03762")
    similar = await client.papers.similar("1706.03762", limit=5)
    resources = await client.papers.resources("1706.03762")
    transcript = await client.papers.transcript("1706.03762")
    bibtex = await client.papers.bibtex("1706.03762")
    pdf_url = await client.papers.pdf_url("1706.03762")
```

`client.papers.full_text(...)` resolves the input to a paper-version UUID and then calls the public `GET /papers/v3/{paperVersion}/full-text` endpoint.

`client.papers.overview_status(...)` resolves the same paper-version UUID and calls the public `GET /papers/v3/{paperVersion}/overview/status` endpoint.

`client.papers.transcript(...)` derives the public podcast transcript URL from the paper's `podcast_path` and fetches `https://paper-podcasts.alphaxiv.org/.../transcript.json` when available.

`client.papers.comments(...)` resolves the paper to a group id and returns typed `PaperComment` trees from the public comments thread endpoint.

Authenticated comment creation and replies are also paper-scoped:

- `await client.papers.create_comment("1706.03762", body="Helpful note")`
- `await client.papers.reply_to_comment("1706.03762", "comment-id", body="Thanks")`

`client.papers.similar(...)` calls the public similar-papers endpoint and deduplicates repeated cards before returning `FeedCard` results. This endpoint expects bare or versioned arXiv identifiers, not UUIDs.

Authenticated paper mutations are also exposed:

- `await client.papers.record_view("1706.03762")`
- `await client.papers.toggle_vote("1706.03762")`

## Assistant

```python
async with AlphaXivClient.from_saved_api_key() as client:
    sessions = await client.assistant.list()
    history = await client.assistant.history(sessions[0].id)
    preferred_model = await client.assistant.preferred_model()
    metadata = await client.assistant.url_metadata("https://github.com/PKU-YuanGroup/Helios")
    run = await client.assistant.ask("Find papers on agent frameworks")
    follow_up = await client.assistant.ask(
        "Focus on the most cited ones.",
        session_id=run.session_id,
        model="gpt-5.4",
    )
```

Paper-scoped assistant chats resolve the paper to a version UUID first:

```python
async with AlphaXivClient.from_saved_api_key() as client:
    run = await client.assistant.ask(
        "Explain the main contribution.",
        paper_id="1706.03762",
    )
```

`client.assistant.stream(...)` yields parsed SSE events from the authenticated assistant transport.

`client.assistant.ask(...)` consumes that stream and returns an `AssistantRun` aggregate with:

- `session_id`
- `variant`
- `paper`
- `model`
- `output_text`
- `reasoning_text`
- `error_message`
- `events`

You can inspect and persist the preferred model separately:

- `await client.assistant.preferred_model()`
- `await client.assistant.set_preferred_model("Claude 4.6 Sonnet")`
- `await client.assistant.url_metadata("https://example.com")`

The client does not expose a trusted live model catalog. It reads the saved preferred model from the authenticated user payload and accepts explicit ids or label-like input for model overrides.

Without auth, assistant methods still raise `AuthRequiredError`.

## Folders And Comment Mutations

```python
async with AlphaXivClient.from_saved_api_key() as client:
    folders = await client.folders.list()
    created = await client.papers.create_comment("1706.03762", body="Helpful note")
    reply = await client.papers.reply_to_comment("1706.03762", created.id, body="Thanks")
    upvote_result = await client.comments.toggle_upvote("comment-id")
    await client.comments.delete("comment-id")
```

`client.folders.list()` returns typed `Folder` objects with nested `FolderPaper` entries.

`client.papers.create_comment(...)` and `client.papers.reply_to_comment(...)` resolve the paper to a version id and return typed `PaperComment` objects. The public interface is intentionally text-only in v1: `body`, optional `title`, and a validated `tag`.

`client.comments.toggle_upvote(...)` returns the raw mutation payload, if the endpoint provides one.

`client.comments.delete(...)` deletes a comment by id and returns `None`.
