from __future__ import annotations

from typing import List, Optional
from urllib.parse import quote

import httpx

from ..._base_client import make_request_options
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, Body, Headers, NotGiven, Query

# AUTOGEN-START create-imports
from ...types.agent.agent import Agent
from ...types.agent.agent_skill_ref import AgentSkillRef
from ...types.agent.context_management_policies_param import ContextManagementPoliciesParam
from ...types.agent.delete_agent_response import DeleteAgentResponse
from ...types.agent.list_agents_response import ListAgentsResponse
from ...types.agent.mcp_server import MCPServer
from ...types.agent.model_config import ModelConfig
from ...types.agent.multiagent_config import MultiagentConfig
from ...types.agent.multiagent_patch import MultiagentPatch
from ...types.agent.tag import Tag
from ...types.agent.tool_item import ToolItem

# AUTOGEN-END create-imports

__all__ = ["Agents", "AsyncAgents"]

_PREFIX = "/agents"


def _list_query(
    *,
    include_archived: bool | NotGiven = NOT_GIVEN,
    limit=NOT_GIVEN,
    page=NOT_GIVEN,
    created_at_gte=NOT_GIVEN,
    created_at_lte=NOT_GIVEN,
) -> dict:
    q: dict = {}
    for k, v in {
        "limit": limit,
        "page": page,
        "created_at_gte": created_at_gte,
        "created_at_lte": created_at_lte,
    }.items():
        if v is not NOT_GIVEN and v is not None:
            q[k] = v
    if include_archived is not NOT_GIVEN and include_archived is not None:
        q["include_archived"] = include_archived
    return q


def _validate_create_multiagent(
    multiagent: MultiagentConfig | NotGiven | None,
) -> MultiagentConfig | NotGiven | None:
    if multiagent is NOT_GIVEN or multiagent is None:
        return multiagent
    return MultiagentConfig.model_validate(multiagent)


class Agents(SyncAPIResource):
    def create(
        self,
        *,
        name: str,
        model: ModelConfig,
        description: Optional[str] | NotGiven = NOT_GIVEN,
        system: Optional[str] | NotGiven = NOT_GIVEN,
        mcp_servers: Optional[List[MCPServer]] | NotGiven = NOT_GIVEN,
        tools: Optional[List[ToolItem]] | NotGiven = NOT_GIVEN,
        skills: Optional[List[AgentSkillRef]] | NotGiven = NOT_GIVEN,
        multiagent: Optional[MultiagentConfig] | NotGiven = NOT_GIVEN,
        metadata: Optional[dict] | NotGiven = NOT_GIVEN,
        tags: Optional[List[Tag]] | NotGiven = NOT_GIVEN,
        # AUTOGEN-START create-kwargs
        context_management: Optional[ContextManagementPoliciesParam] | NotGiven = NOT_GIVEN,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> Agent:
        multiagent = _validate_create_multiagent(multiagent)
        return self._post(
            _PREFIX,
            body=dump_body(
                {
                    "name": name,
                    "model": model,
                    "description": description,
                    "system": system,
                    "mcp_servers": mcp_servers,
                    "tools": tools,
                    "skills": skills,
                    "multiagent": multiagent,
                    "metadata": metadata,
                    "tags": tags,
                    # AUTOGEN-START create-body
                    "context_management": context_management,
                    # AUTOGEN-END create-body
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    def retrieve(
        self,
        agent_id: str,
        *,
        version: Optional[int] | NotGiven = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Agent:
        if not agent_id:
            raise ValueError("agent_id is required")
        query: dict = {}
        if version is not NOT_GIVEN and version is not None:
            query["version"] = version
        return self._get(
            f"{_PREFIX}/{agent_id}",
            options=make_request_options(
                query=query or None,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=Agent,
        )

    def list(
        self,
        *,
        include_archived: bool | NotGiven = NOT_GIVEN,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        created_at_gte=NOT_GIVEN,
        created_at_lte=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListAgentsResponse:
        return self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(
                    include_archived=include_archived,
                    limit=limit,
                    page=page,
                    created_at_gte=created_at_gte,
                    created_at_lte=created_at_lte,
                ),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListAgentsResponse,
        )

    def update(
        self,
        agent_id: str,
        *,
        version: int,
        name: Optional[str] | NotGiven = NOT_GIVEN,
        model: Optional[ModelConfig] | NotGiven = NOT_GIVEN,
        description: Optional[str] | NotGiven = NOT_GIVEN,
        system: Optional[str] | NotGiven = NOT_GIVEN,
        mcp_servers: Optional[List[MCPServer]] | NotGiven = NOT_GIVEN,
        tools: Optional[List[ToolItem]] | NotGiven = NOT_GIVEN,
        skills: Optional[List[AgentSkillRef]] | NotGiven = NOT_GIVEN,
        multiagent: Optional[MultiagentPatch] | NotGiven = NOT_GIVEN,
        metadata: Optional[dict] | NotGiven = NOT_GIVEN,
        # AUTOGEN-START update-kwargs
        context_management: Optional[ContextManagementPoliciesParam] | NotGiven = NOT_GIVEN,
        # AUTOGEN-END update-kwargs
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Agent:
        if not agent_id:
            raise ValueError("agent_id is required")
        return self._post(
            f"{_PREFIX}/{agent_id}",
            body=dump_body(
                {
                    "version": version,
                    "name": name,
                    "model": model,
                    "description": description,
                    "system": system,
                    "mcp_servers": mcp_servers,
                    "tools": tools,
                    "skills": skills,
                    "multiagent": multiagent,
                    "metadata": metadata,
                    # AUTOGEN-START update-body
                    "context_management": context_management,
                    # AUTOGEN-END update-body
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    def delete(
        self, agent_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteAgentResponse:
        if not agent_id:
            raise ValueError("agent_id is required")
        return self._delete(
            f"{_PREFIX}/{agent_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteAgentResponse,
        )

    def list_versions(
        self,
        agent_id: str,
        *,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListAgentsResponse:
        if not agent_id:
            raise ValueError("agent_id is required")
        q: dict = {}
        if limit is not NOT_GIVEN and limit is not None:
            q["limit"] = limit
        if page is not NOT_GIVEN and page is not None:
            q["page"] = page
        return self._get(
            f"{_PREFIX}/{agent_id}/versions",
            options=make_request_options(
                query=q, extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListAgentsResponse,
        )

    def archive(self, agent_id: str, *, extra_headers=None, extra_query=None, timeout=None) -> Agent:
        """Archive this agent; the POST has no request body."""
        if not agent_id:
            raise ValueError("agent_id is required")
        return self._post(
            f"{_PREFIX}/{quote(agent_id, safe='')}/archive",
            # Raw empty bytes bypass the client's default empty JSON object.
            body=b"",  # type: ignore[arg-type]
            options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, timeout=timeout),
            cast_to=Agent,
        )


class AsyncAgents(AsyncAPIResource):
    async def create(
        self,
        *,
        name: str,
        model: ModelConfig,
        description=NOT_GIVEN,
        system=NOT_GIVEN,
        mcp_servers=NOT_GIVEN,
        tools=NOT_GIVEN,
        skills=NOT_GIVEN,
        multiagent=NOT_GIVEN,
        metadata=NOT_GIVEN,
        tags=NOT_GIVEN,
        # AUTOGEN-START create-kwargs
        context_management: Optional[ContextManagementPoliciesParam] | NotGiven = NOT_GIVEN,
        # AUTOGEN-END create-kwargs
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Agent:
        multiagent = _validate_create_multiagent(multiagent)
        return await self._post(
            _PREFIX,
            body=dump_body(
                {
                    "name": name,
                    "model": model,
                    "description": description,
                    "system": system,
                    "mcp_servers": mcp_servers,
                    "tools": tools,
                    "skills": skills,
                    "multiagent": multiagent,
                    "metadata": metadata,
                    "tags": tags,
                    # AUTOGEN-START create-body
                    "context_management": context_management,
                    # AUTOGEN-END create-body
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    async def retrieve(
        self,
        agent_id: str,
        *,
        version: Optional[int] | NotGiven = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Agent:
        if not agent_id:
            raise ValueError("agent_id is required")
        query: dict = {}
        if version is not NOT_GIVEN and version is not None:
            query["version"] = version
        return await self._get(
            f"{_PREFIX}/{agent_id}",
            options=make_request_options(
                query=query or None,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=Agent,
        )

    async def list(
        self,
        *,
        include_archived: bool | NotGiven = NOT_GIVEN,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        created_at_gte=NOT_GIVEN,
        created_at_lte=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListAgentsResponse:
        return await self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(
                    include_archived=include_archived,
                    limit=limit,
                    page=page,
                    created_at_gte=created_at_gte,
                    created_at_lte=created_at_lte,
                ),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListAgentsResponse,
        )

    async def update(
        self,
        agent_id: str,
        *,
        version: int,
        name=NOT_GIVEN,
        model=NOT_GIVEN,
        description=NOT_GIVEN,
        system=NOT_GIVEN,
        mcp_servers=NOT_GIVEN,
        tools=NOT_GIVEN,
        skills=NOT_GIVEN,
        multiagent=NOT_GIVEN,
        metadata=NOT_GIVEN,
        # AUTOGEN-START update-kwargs
        context_management: Optional[ContextManagementPoliciesParam] | NotGiven = NOT_GIVEN,
        # AUTOGEN-END update-kwargs
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Agent:
        if not agent_id:
            raise ValueError("agent_id is required")
        return await self._post(
            f"{_PREFIX}/{agent_id}",
            body=dump_body(
                {
                    "version": version,
                    "name": name,
                    "model": model,
                    "description": description,
                    "system": system,
                    "mcp_servers": mcp_servers,
                    "tools": tools,
                    "skills": skills,
                    "multiagent": multiagent,
                    "metadata": metadata,
                    # AUTOGEN-START update-body
                    "context_management": context_management,
                    # AUTOGEN-END update-body
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    async def delete(
        self, agent_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteAgentResponse:
        if not agent_id:
            raise ValueError("agent_id is required")
        return await self._delete(
            f"{_PREFIX}/{agent_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteAgentResponse,
        )

    async def list_versions(
        self,
        agent_id: str,
        *,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListAgentsResponse:
        if not agent_id:
            raise ValueError("agent_id is required")
        q: dict = {}
        if limit is not NOT_GIVEN and limit is not None:
            q["limit"] = limit
        if page is not NOT_GIVEN and page is not None:
            q["page"] = page
        return await self._get(
            f"{_PREFIX}/{agent_id}/versions",
            options=make_request_options(
                query=q, extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListAgentsResponse,
        )

    async def archive(self, agent_id: str, *, extra_headers=None, extra_query=None, timeout=None) -> Agent:
        """Archive this agent; the POST has no request body."""
        if not agent_id:
            raise ValueError("agent_id is required")
        return await self._post(
            f"{_PREFIX}/{quote(agent_id, safe='')}/archive",
            # Raw empty bytes bypass the client's default empty JSON object.
            body=b"",  # type: ignore[arg-type]
            options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, timeout=timeout),
            cast_to=Agent,
        )
