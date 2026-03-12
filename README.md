# alphaxiv-py

`alphaxiv-py` is a Python SDK and CLI for alphaXiv.

This v1 release is intentionally public-first. It supports:

- API-key auth via `ALPHAXIV_API_KEY` or locally saved bearer auth
- optional browser-assisted login for capturing the current alphaXiv web token
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

Authenticated features use direct HTTP bearer auth against `api.alphaxiv.org`. The recommended setup is an alphaXiv API key exposed through `ALPHAXIV_API_KEY` or saved locally with `alphaxiv login --api-key ...`. Browser automation is optional and only used when you explicitly run `alphaxiv login` without an API key. The client reads the current preferred model live from `GET /users/v3` and writes changes through `PATCH /users/v3/preferences`; it does not claim to know the full current model catalog.

## Installation

```bash
uv pip install -e .
```

No browser dependencies are required for normal CLI or SDK usage.

Recommended auth setup:

```bash
export ALPHAXIV_API_KEY="axv1_..."
alphaxiv assistant list
```

If you prefer to save the key locally:

```bash
alphaxiv login --api-key "$ALPHAXIV_API_KEY"
```

Browser login support is optional and only needed for `alphaxiv login` without `--api-key`:

```bash
uv sync --extra browser
uv run playwright install chromium
```

That flow launches a visible Chromium window. A headless browser is not required for normal API-key usage.

## CLI Quick Start

```bash
export ALPHAXIV_API_KEY="axv1_..."
alphaxiv login --api-key "$ALPHAXIV_API_KEY"
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
import os

from alphaxiv import AlphaXivClient


async def main() -> None:
    async with AlphaXivClient(api_key=os.environ["ALPHAXIV_API_KEY"]) as client:
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

`AlphaXivClient.from_saved_auth()` also works with `ALPHAXIV_API_KEY` and then falls back to locally saved auth.

## Docs

- [CLI reference](docs/cli-reference.md)
- [Python API](docs/python-api.md)
- [Development](docs/development.md)
- [API inventory](docs/api-inventory.md)
