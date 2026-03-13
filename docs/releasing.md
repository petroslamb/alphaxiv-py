# Releasing

This project uses `pyproject.toml` as the source of truth for the package version.

Runtime version reporting comes from installed package metadata, so version bumps only need to change:

- `pyproject.toml`
- `CHANGELOG.md`

## Release Steps

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv build
uvx twine check dist/*
git tag v<version>
git push origin main --tags
```

For GitHub releases, attach the built files from `dist/`.

PyPI publishing is not automated yet. The recommended next step is to configure PyPI Trusted Publishing for this repository and add a release workflow that publishes tagged builds.
