from __future__ import annotations

from ..._base_client import make_request_options
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN
from ...types.vault.credential import Credential
from ...types.vault.credential_auth import CredentialAuth
from ...types.vault.credential_validation import CredentialValidation
from ...types.vault.delete_credential_response import DeleteCredentialResponse
from ...types.vault.list_credentials_response import ListCredentialsResponse

__all__ = ["Credentials", "AsyncCredentials"]


def _prefix(vault_id: str) -> str:
    return f"/vaults/{vault_id}/credentials"


def _list_query(*, limit=NOT_GIVEN, page=NOT_GIVEN) -> dict:
    q: dict = {}
    for k, v in {"limit": limit, "page": page}.items():
        if v is not NOT_GIVEN and v is not None:
            q[k] = v
    return q


class Credentials(SyncAPIResource):
    def create(
        self,
        vault_id: str,
        *,
        auth: CredentialAuth,
        display_name=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Credential:
        if not vault_id:
            raise ValueError("vault_id is required")
        return self._post(
            _prefix(vault_id),
            body=dump_body({"auth": auth, "display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Credential,
        )

    def retrieve(
        self, vault_id: str, credential_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Credential:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return self._get(
            f"{_prefix(vault_id)}/{credential_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Credential,
        )

    def list(
        self,
        vault_id: str,
        *,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListCredentialsResponse:
        if not vault_id:
            raise ValueError("vault_id is required")
        return self._get(
            _prefix(vault_id),
            options=make_request_options(
                query=_list_query(limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListCredentialsResponse,
        )

    def update(
        self,
        vault_id: str,
        credential_id: str,
        *,
        auth=NOT_GIVEN,
        display_name=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Credential:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return self._post(
            f"{_prefix(vault_id)}/{credential_id}",
            body=dump_body({"auth": auth, "display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Credential,
        )

    def delete(
        self, vault_id: str, credential_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteCredentialResponse:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return self._delete(
            f"{_prefix(vault_id)}/{credential_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteCredentialResponse,
        )

    def validate(
        self, vault_id: str, credential_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> CredentialValidation:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return self._post(
            f"{_prefix(vault_id)}/{credential_id}/mcp_oauth_validate",
            body=None,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CredentialValidation,
        )


class AsyncCredentials(AsyncAPIResource):
    async def create(
        self,
        vault_id: str,
        *,
        auth: CredentialAuth,
        display_name=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Credential:
        if not vault_id:
            raise ValueError("vault_id is required")
        return await self._post(
            _prefix(vault_id),
            body=dump_body({"auth": auth, "display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Credential,
        )

    async def retrieve(
        self, vault_id: str, credential_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Credential:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return await self._get(
            f"{_prefix(vault_id)}/{credential_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Credential,
        )

    async def list(
        self,
        vault_id: str,
        *,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListCredentialsResponse:
        if not vault_id:
            raise ValueError("vault_id is required")
        return await self._get(
            _prefix(vault_id),
            options=make_request_options(
                query=_list_query(limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListCredentialsResponse,
        )

    async def update(
        self,
        vault_id: str,
        credential_id: str,
        *,
        auth=NOT_GIVEN,
        display_name=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Credential:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return await self._post(
            f"{_prefix(vault_id)}/{credential_id}",
            body=dump_body({"auth": auth, "display_name": display_name, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Credential,
        )

    async def delete(
        self, vault_id: str, credential_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteCredentialResponse:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return await self._delete(
            f"{_prefix(vault_id)}/{credential_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteCredentialResponse,
        )

    async def validate(
        self, vault_id: str, credential_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> CredentialValidation:
        if not vault_id or not credential_id:
            raise ValueError("vault_id and credential_id are required")
        return await self._post(
            f"{_prefix(vault_id)}/{credential_id}/mcp_oauth_validate",
            body=None,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CredentialValidation,
        )
