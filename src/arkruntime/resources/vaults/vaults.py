from __future__ import annotations

from ..._base_client import make_request_options
from ..._compat import cached_property
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN
from ...types.vault.delete_vault_response import DeleteVaultResponse
from ...types.vault.list_vaults_response import ListVaultsResponse
from ...types.vault.vault import Vault
from .credentials import AsyncCredentials, Credentials

__all__ = ["Vaults", "AsyncVaults"]

_PREFIX = "/vaults"


def _list_query(*, limit=NOT_GIVEN, page=NOT_GIVEN) -> dict:
    q: dict = {}
    for k, v in {"limit": limit, "page": page}.items():
        if v is not NOT_GIVEN and v is not None:
            q[k] = v
    return q


class Vaults(SyncAPIResource):
    @cached_property
    def credentials(self) -> Credentials:
        return Credentials(self._client)

    def create(
        self,
        *,
        display_name: str,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Vault:
        return self._post(
            _PREFIX,
            body=dump_body({"display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Vault,
        )

    def retrieve(self, vault_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None) -> Vault:
        if not vault_id:
            raise ValueError("vault_id is required")
        return self._get(
            f"{_PREFIX}/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Vault,
        )

    def list(
        self, *, limit=NOT_GIVEN, page=NOT_GIVEN, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> ListVaultsResponse:
        return self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListVaultsResponse,
        )

    def update(
        self,
        vault_id: str,
        *,
        display_name=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Vault:
        if not vault_id:
            raise ValueError("vault_id is required")
        return self._post(
            f"{_PREFIX}/{vault_id}",
            body=dump_body({"display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Vault,
        )

    def delete(
        self, vault_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteVaultResponse:
        if not vault_id:
            raise ValueError("vault_id is required")
        return self._delete(
            f"{_PREFIX}/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteVaultResponse,
        )


class AsyncVaults(AsyncAPIResource):
    @cached_property
    def credentials(self) -> AsyncCredentials:
        return AsyncCredentials(self._client)

    async def create(
        self,
        *,
        display_name: str,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Vault:
        return await self._post(
            _PREFIX,
            body=dump_body({"display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Vault,
        )

    async def retrieve(
        self, vault_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Vault:
        if not vault_id:
            raise ValueError("vault_id is required")
        return await self._get(
            f"{_PREFIX}/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Vault,
        )

    async def list(
        self, *, limit=NOT_GIVEN, page=NOT_GIVEN, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> ListVaultsResponse:
        return await self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListVaultsResponse,
        )

    async def update(
        self,
        vault_id: str,
        *,
        display_name=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Vault:
        if not vault_id:
            raise ValueError("vault_id is required")
        return await self._post(
            f"{_PREFIX}/{vault_id}",
            body=dump_body({"display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Vault,
        )

    async def delete(
        self, vault_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteVaultResponse:
        if not vault_id:
            raise ValueError("vault_id is required")
        return await self._delete(
            f"{_PREFIX}/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteVaultResponse,
        )
