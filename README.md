# alphaxiv-py

`alphaxiv-py` is a Python SDK and CLI for alphaXiv.

This v1 release is intentionally public-first. It supports:

- browser-assisted alphaXiv login with saved bearer auth
- authenticated assistant chat for homepage and paper-scoped sessions
- homepage search suggestions for papers, topics, and organizations
- homepage feed/card retrieval with sort and filter support
- bare and versioned arXiv ID resolution
- paper metadata
- paper full text
- AI overview/blog payloads
- overview status and translation availability
- mentions/resources aggregation
- podcast transcript retrieval
- PDF URL lookup and download
- CLI context around a current paper

The login flow is still browser-assisted because alphaXiv uses Clerk in the web app. Once logged in, assistant chat uses direct authenticated API calls plus SSE streaming rather than Playwright UI automation. The client reads the current preferred model live from `GET /users/v3` and writes changes through `PATCH /users/v3/preferences`; it does not claim to know the full current model catalog.

## Installation

```bash
uv pip install -e .
```

Browser login support is optional:

```bash
uv sync --extra browser
uv run playwright install chromium
```

## CLI Quick Start

```bash
alphaxiv login
alphaxiv search "graph neural networks for molecules"
alphaxiv search-papers "graph neural networks for molecules"
alphaxiv search-organizations "graph neural networks for molecules"
alphaxiv search-topics "graph neural networks for molecules"
alphaxiv assistant list
alphaxiv assistant set-model "Claude 4.6 Sonnet"
alphaxiv assistant start "Find papers on agent frameworks"
alphaxiv assistant start --model "GPT 5.4" "Find papers on agent frameworks"
alphaxiv assistant reply "Focus on the most cited ones"
alphaxiv assistant history
alphaxiv feed filters
alphaxiv feed list --sort likes --limit 5
alphaxiv feed list --organization MIT --source twitter --limit 5
alphaxiv use 2603.04379
alphaxiv status
alphaxiv logout
alphaxiv paper show
alphaxiv paper text --page 1
alphaxiv overview
alphaxiv overview --machine
alphaxiv overview-status
alphaxiv resources
alphaxiv resources --bibtex
alphaxiv resources --transcript
alphaxiv pdf url
alphaxiv pdf download ./helios.pdf
```

## Python Quick Start

```python
import asyncio

from alphaxiv import AlphaXivClient


async def main() -> None:
    async with AlphaXivClient.from_saved_auth() as client:
        homepage = await client.search.homepage("graph neural networks for molecules")
        print(homepage.papers[0].paper_id, homepage.papers[0].title)

        papers = await client.search.papers("graph neural networks for molecules")
        organizations = await client.search.organizations("graph neural networks for molecules")
        topics = await client.search.closest_topics("graph neural networks for molecules")
        print(papers[0].paper_id, organizations[0].name, topics[0])

        cards = await client.explore.feed(sort="Likes", limit=3)
        print(cards[0].paper_id, cards[0].upvotes)

        paper = await client.papers.get("2603.04379")
        print(paper.version.title)

        full_text = await client.papers.full_text("2603.04379")
        print(full_text.pages[0].text[:200])

        overview = await client.papers.overview("2603.04379")
        print(overview.summary.summary if overview.summary else overview.title)

        status = await client.papers.overview_status("2603.04379")
        print(status.state, sorted(status.translations))

        transcript = await client.papers.transcript("2603.04379")
        print(transcript.lines[0].speaker, transcript.lines[0].line[:80])

        sessions = await client.assistant.list()
        print(sessions[0].id, sessions[0].title)

        run = await client.assistant.ask("Find papers on agent frameworks")
        print(run.session_id, run.output_text[:120])


asyncio.run(main())
```

If you have not run `alphaxiv login`, `AlphaXivClient.from_saved_auth()` behaves like an anonymous client.

## Docs

- [CLI reference](docs/cli-reference.md)
- [Python API](docs/python-api.md)
- [Development](docs/development.md)
