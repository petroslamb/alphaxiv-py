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

## PyPI Trusted Publishing

This repository now includes a publish workflow at:

- `.github/workflows/publish.yml`

It uses PyPI Trusted Publishing through `pypa/gh-action-pypi-publish` and the GitHub environment:

- `pypi`

To enable publishing on PyPI, configure a trusted publisher for this project using the official PyPI flow:

- Existing project: [Adding a Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
- New project: [Creating a project through OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)

Use these values in PyPI:

- PyPI project name: `alphaxiv-py`
- GitHub owner: `petroslamb`
- GitHub repository: `alphaxiv-py`
- Workflow filename: `publish.yml`
- Environment name: `pypi`

After PyPI is configured, publishing can happen either by:

- pushing a version tag like `v0.1.0`
- running the `Publish` workflow manually from GitHub Actions

PyPI's official GitHub Actions guidance for Trusted Publishing is here:

- [Publishing with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
