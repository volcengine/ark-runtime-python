from __future__ import annotations

from typing import List, Optional

import httpx

from ..._base_client import make_request_options
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from ...types.agent.agent import Agent
from ...types.agent.agent_skill_ref import AgentSkillRef
from ...types.agent.delete_agent_response import DeleteAgentResponse
from ...types.agent.list_agents_response import ListAgentsResponse
from ...types.agent.mcp_server import MCPServer
from ...types.agent.model_config import ModelConfig
from ...types.agent.multiagent_config import MultiagentConfig
from ...types.agent.tag import Tag
from ...types.agent.tool_item import ToolItem

__all__ = ["Agents", "AsyncAgents"]

_PREFIX = "/agents"


def _list_query(
    *,
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
    return q


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
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> Agent:
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
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    def retrieve(self, agent_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None) -> Agent:
        if not agent_id:
            raise ValueError("agent_id is required")
        return self._get(
            f"{_PREFIX}/{agent_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    def list(
        self,
        *,
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
        multiagent: Optional[MultiagentConfig] | NotGiven = NOT_GIVEN,
        metadata: Optional[dict] | NotGiven = NOT_GIVEN,
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
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Agent:
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
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    async def retrieve(
        self, agent_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Agent:
        if not agent_id:
            raise ValueError("agent_id is required")
        return await self._get(
            f"{_PREFIX}/{agent_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    async def list(
        self,
        *,
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
