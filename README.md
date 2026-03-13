# alphaxiv-py

`alphaxiv-py` is a Python SDK and CLI for alphaXiv.

This v1 release is intentionally public-first. It supports:

- API-key auth via `ALPHAXIV_API_KEY` or a locally saved alphaXiv API key
- authenticated assistant chat for homepage and paper-scoped sessions
- homepage search suggestions for papers, topics, and organizations
- homepage feed/card retrieval with sort and filter support
- bare and versioned arXiv ID resolution
- paper metadata
- public paper comments
- paper full text
- AI overview/blog payloads
- overview status and translation availability
- similar-paper recommendations
- mentions/resources aggregation
- podcast transcript retrieval
- PDF URL lookup and download
- authenticated folder listing
- authenticated assistant URL metadata lookup
- authenticated paper votes plus comment create, reply, delete, and upvote mutations
- CLI context around a current paper and assistant session

Authenticated features use direct HTTP bearer auth against `api.alphaxiv.org`. The recommended setup is an alphaXiv API key exposed through `ALPHAXIV_API_KEY` or saved locally with `alphaxiv auth set-api-key`. The client reads the current preferred model live from `GET /users/v3` and writes changes through `PATCH /users/v3/preferences`; it does not claim to know the full current model catalog.

## Installation

```bash
uv add alphaxiv-py
```

or

```bash
pip install alphaxiv-py
```

For local development:

```bash
uv pip install -e .
```

Recommended auth setup:

```bash
export ALPHAXIV_API_KEY="axv1_..."
alphaxiv assistant list
```

If you prefer to save the key locally:

```bash
alphaxiv auth set-api-key --api-key "$ALPHAXIV_API_KEY"
```

Users create API keys in the alphaXiv web app. This package does not create or manage API keys remotely.

## CLI Quick Start

The CLI is resource-first. The top-level surface is grouped into `auth`, `context`, `search`,
`feed`, `paper`, `assistant`, and `folders`.

```bash
export ALPHAXIV_API_KEY="axv1_..."
alphaxiv auth set-api-key --api-key "$ALPHAXIV_API_KEY"
alphaxiv auth status
alphaxiv context use paper 2603.04379
alphaxiv context show
alphaxiv search all "graph neural networks for molecules"
alphaxiv search papers "graph neural networks for molecules"
alphaxiv search organizations "graph neural networks for molecules"
alphaxiv search topics "graph neural networks for molecules"
alphaxiv assistant list
alphaxiv assistant model
alphaxiv assistant url-metadata https://github.com/PKU-YuanGroup/Helios
alphaxiv assistant set-model "Claude 4.6 Sonnet"
alphaxiv assistant start "Find papers on agent frameworks"
alphaxiv assistant start --model "GPT 5.4" "Find papers on agent frameworks"
alphaxiv assistant reply "Focus on the most cited ones"
alphaxiv assistant history
alphaxiv feed filters
alphaxiv feed filters search "agentic"
alphaxiv feed list --sort likes --limit 5
alphaxiv feed list --organization MIT --source twitter --limit 5
alphaxiv feed list --topic agentic-frameworks --organization Meta --limit 5
alphaxiv paper show
alphaxiv paper abstract
alphaxiv paper summary
alphaxiv paper comments list
alphaxiv paper comments add --body "Helpful note"
alphaxiv paper comments reply <comment-id> --body "Thanks"
alphaxiv paper comments upvote <comment-id> --yes
alphaxiv paper comments delete <comment-id> --yes
alphaxiv paper similar --limit 5
alphaxiv paper text --page 1
alphaxiv paper vote --yes
alphaxiv paper view --yes
alphaxiv paper overview
alphaxiv paper overview --machine
alphaxiv paper overview-status
alphaxiv paper resources
alphaxiv paper resources --bibtex
alphaxiv paper resources --transcript
alphaxiv paper pdf url
alphaxiv paper pdf download ./helios.pdf
alphaxiv folders list --papers
alphaxiv context clear
alphaxiv auth clear
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

        filter_search = await client.explore.search_filters("agentic")
        print(filter_search.topics[:2], [item.name for item in filter_search.organizations[:2]])

        cards = await client.explore.feed(
            sort="most-stars",
            source="GitHub",
            topics=("agentic-frameworks",),
            limit=3,
        )
        print(cards[0].paper_id, cards[0].upvotes)

        paper = await client.papers.get("2603.04379")
        print(paper.version.title)

        comments = await client.papers.comments("2603.04379")
        print(comments[0].body if comments else "no comments")

        full_text = await client.papers.full_text("2603.04379")
        print(full_text.pages[0].text[:200])

        overview = await client.papers.overview("2603.04379")
        print(overview.summary.summary if overview.summary else overview.title)

        status = await client.papers.overview_status("2603.04379")
        print(status.state, sorted(status.translations))

        transcript = await client.papers.transcript("2603.04379")
        print(transcript.lines[0].speaker, transcript.lines[0].line[:80])

        similar = await client.papers.similar("2603.04379", limit=3)
        print([card.paper_id for card in similar])

        sessions = await client.assistant.list()
        print(sessions[0].id, sessions[0].title)

        metadata = await client.assistant.url_metadata("https://github.com/PKU-YuanGroup/Helios")
        print(metadata.title)

        folders = await client.folders.list()
        print(folders[0].name if folders else "no folders")

        run = await client.assistant.ask("Find papers on agent frameworks")
        print(run.session_id, run.output_text[:120])


asyncio.run(main())
```

`AlphaXivClient.from_saved_api_key()` loads `ALPHAXIV_API_KEY` first and then falls back to `~/.alphaxiv/api-key.json`.

## Docs

- [CLI reference](docs/cli-reference.md)
- [Python API](docs/python-api.md)
- [Development](docs/development.md)
- [Releasing](docs/releasing.md)
- [API inventory](docs/api-inventory.md)
