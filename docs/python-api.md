# Python API

## Client

```python
from alphaxiv import AlphaXivClient
```

Use `AlphaXivClient` as an async context manager.

If you have already signed in with `alphaxiv login`, you can reuse the saved bearer token:

```python
async with AlphaXivClient.from_saved_auth() as client:
    results = await client.search.papers("attention is all you need")
```

`AlphaXivClient.from_saved_auth()` also refreshes expired saved tokens from the persisted browser profile when possible.

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
    cards = await client.explore.feed(
        sort="Likes",
        organizations=("MIT",),
        source="Twitter (X)",
        limit=5,
    )
```

## Papers

```python
async with AlphaXivClient() as client:
    resolved = await client.papers.resolve("1706.03762")
    paper = await client.papers.get("1706.03762")
    full_text = await client.papers.full_text("1706.03762")
    overview = await client.papers.overview("1706.03762")
    overview_status = await client.papers.overview_status("1706.03762")
    mentions = await client.papers.mentions("1706.03762")
    resources = await client.papers.resources("1706.03762")
    transcript = await client.papers.transcript("1706.03762")
    bibtex = await client.papers.bibtex("1706.03762")
    pdf_url = await client.papers.pdf_url("1706.03762")
```

`client.papers.full_text(...)` resolves the input to a paper-version UUID and then calls the public `GET /papers/v3/{paperVersion}/full-text` endpoint.

`client.papers.overview_status(...)` resolves the same paper-version UUID and calls the public `GET /papers/v3/{paperVersion}/overview/status` endpoint.

`client.papers.transcript(...)` derives the public podcast transcript URL from the paper's `podcast_path` and fetches `https://paper-podcasts.alphaxiv.org/.../transcript.json` when available.

## Assistant

```python
async with AlphaXivClient.from_saved_auth() as client:
    sessions = await client.assistant.list()
    history = await client.assistant.history(sessions[0].id)
    preferred_model = await client.assistant.preferred_model()
    run = await client.assistant.ask("Find papers on agent frameworks")
    follow_up = await client.assistant.ask(
        "Focus on the most cited ones.",
        session_id=run.session_id,
        model="gpt-5.4",
    )
```

Paper-scoped assistant chats resolve the paper to a version UUID first:

```python
async with AlphaXivClient.from_saved_auth() as client:
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

The client does not expose a trusted live model catalog. It reads the saved preferred model from the authenticated user payload and accepts explicit ids or label-like input for model overrides.

Without auth, assistant methods still raise `AuthRequiredError`.
