"""Authenticated folders support for alphaXiv."""

from __future__ import annotations

import builtins
from collections.abc import Sequence

from ._core import BASE_API_URL, ClientCore
from .exceptions import AlphaXivError, AuthRequiredError
from .types import Folder

FOLDERS_AUTH_REQUIRED_MESSAGE = (
    "alphaXiv folder endpoints require an API key. Set ALPHAXIV_API_KEY, run "
    "'alphaxiv auth set-api-key', or pass api_key into AlphaXivClient(...)."
)


class FoldersAPI:
    """Authenticated folder operations for alphaXiv."""

    def __init__(self, core: ClientCore) -> None:
        self._core = core

    async def list(self) -> list[Folder]:
        self._require_auth()
        payload = await self._core.get_json(f"{BASE_API_URL}/folders/v3")
        if not isinstance(payload, list):
            raise AlphaXivError("Unexpected folders payload.")
        return [Folder.from_payload(item) for item in payload if isinstance(item, dict)]

    async def get(self, selector: str) -> Folder:
        folders = await self.list()
        return self._resolve_selector(folders, selector)

    async def add_papers(self, folder: str, paper_group_ids: Sequence[str]) -> Folder:
        self._require_auth()
        target = await self.get(folder)
        normalized_ids = self._normalize_paper_group_ids(paper_group_ids)
        await self._core.request(
            "POST",
            f"{BASE_API_URL}/folders/v3/{target.id}/add-papers",
            json_data={"paperGroupIds": normalized_ids},
        )
        return await self.get(target.id)

    async def remove_papers(self, folder: str, paper_group_ids: Sequence[str]) -> Folder:
        self._require_auth()
        target = await self.get(folder)
        normalized_ids = self._normalize_paper_group_ids(paper_group_ids)
        await self._core.request(
            "POST",
            f"{BASE_API_URL}/folders/v3/{target.id}/remove-papers",
            json_data={"paperGroupIds": normalized_ids},
        )
        return await self.get(target.id)

    def _require_auth(self) -> None:
        if not self._core.authorization:
            raise AuthRequiredError(FOLDERS_AUTH_REQUIRED_MESSAGE)

    def _resolve_selector(self, folders: Sequence[Folder], selector: str) -> Folder:
        normalized = selector.strip()
        if not normalized:
            raise AlphaXivError("Folder selector must not be empty.")

        for folder in folders:
            if folder.id == normalized:
                return folder

        casefolded = normalized.casefold()
        exact_name_matches = [folder for folder in folders if folder.name.casefold() == casefolded]
        if len(exact_name_matches) == 1:
            return exact_name_matches[0]
        if len(exact_name_matches) > 1:
            raise AlphaXivError(
                "Folder selector matched multiple folders: "
                + ", ".join(f"{folder.id} ({folder.name})" for folder in exact_name_matches)
            )

        partial_matches = [
            folder
            for folder in folders
            if casefolded in folder.name.casefold() or folder.id.startswith(normalized)
        ]
        if len(partial_matches) == 1:
            return partial_matches[0]
        if len(partial_matches) > 1:
            raise AlphaXivError(
                "Folder selector matched multiple folders: "
                + ", ".join(f"{folder.id} ({folder.name})" for folder in partial_matches)
            )

        raise AlphaXivError(f"No alphaXiv folder matched '{selector}'.")

    def _normalize_paper_group_ids(self, paper_group_ids: Sequence[str]) -> builtins.list[str]:
        normalized_ids: builtins.list[str] = []
        seen: set[str] = set()
        for paper_group_id in paper_group_ids:
            cleaned = paper_group_id.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            normalized_ids.append(cleaned)
        if not normalized_ids:
            raise AlphaXivError("At least one paper group id is required.")
        return normalized_ids
