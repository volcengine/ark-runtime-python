from __future__ import annotations

from typing import BinaryIO, Optional, Tuple, Union

from ..._base_client import make_request_options
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, NotGiven
from ...types.skill.skill import Skill

__all__ = ["Skills", "AsyncSkills"]

_PREFIX = "/skills"

# Multipart upload signature: caller passes either a file-like `BinaryIO` or
# an `(filename, fileobj_or_bytes)` tuple; the underlying httpx-based
# transport packs it as `files={"files": (filename, fileobj_or_bytes)}`.
FileArg = Union[BinaryIO, bytes, Tuple[str, Union[BinaryIO, bytes]]]


def _files_kwarg(files: FileArg) -> dict:
    # Normalize into httpx's `files=` mapping. Server-side field name is
    # fixed to "files" (see typespec/skill/request.tsp).
    if isinstance(files, tuple) and len(files) == 2:
        return {"files": files}
    return {"files": ("skill.zip", files)}


def _multipart_headers(extra_headers):
    # Signals the base client to emit multipart/form-data; the base transport
    # then reads `body=` as form fields and `files=` as file parts. Follows
    # the same pattern as the existing Files.create wrapper.
    return {"Content-Type": "multipart/form-data", **(extra_headers or {})}


class Skills(SyncAPIResource):
    def create(
        self,
        *,
        files: FileArg,
        display_title: Optional[str] | NotGiven = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Skill:
        body: dict = {}
        if display_title is not NOT_GIVEN and display_title is not None:
            body["display_title"] = display_title
        return self._post(
            _PREFIX,
            body=body,
            files=_files_kwarg(files),
            options=make_request_options(
                extra_headers=_multipart_headers(extra_headers),
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=Skill,
        )

    def retrieve(self, skill_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None) -> Skill:
        if not skill_id:
            raise ValueError("skill_id is required")
        return self._get(
            f"{_PREFIX}/{skill_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Skill,
        )


class AsyncSkills(AsyncAPIResource):
    async def create(
        self,
        *,
        files: FileArg,
        display_title=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Skill:
        body: dict = {}
        if display_title is not NOT_GIVEN and display_title is not None:
            body["display_title"] = display_title
        return await self._post(
            _PREFIX,
            body=body,
            files=_files_kwarg(files),
            options=make_request_options(
                extra_headers=_multipart_headers(extra_headers),
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=Skill,
        )

    async def retrieve(
        self, skill_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Skill:
        if not skill_id:
            raise ValueError("skill_id is required")
        return await self._get(
            f"{_PREFIX}/{skill_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Skill,
        )
