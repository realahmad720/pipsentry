"""Generic MCP Connector Framework (Section 20): a user registers any MCP
server's endpoint URL + credentials; on registration (and on each scheduled
health check) we call its tool-discovery endpoint and record what it
exposes — no code change needed per new server.

Actually calling a discovered tool's arbitrary, unknown-shaped output inside
Agent 1/2's structured reasoning pass is a separate, harder problem (safely
feeding an arbitrary schema into a prompt that must still produce our fixed
advisory shape) and isn't wired in here. What *is* wired in: discovery,
health, and category tagging, so the Reasoning Trail panel (Section 20) can
truthfully say which connected sources exist and whether they're reachable.
That's the honest subset of "dynamically pull in connected MCP tools" this
pass implements.
"""

import asyncio

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.core.crypto import decrypt


class ConnectorUnreachable(Exception):
    pass


async def _discover_tools_async(endpoint_url: str, credentials: str | None) -> list[dict]:
    headers = {"Authorization": credentials} if credentials else {}
    async with httpx2.AsyncClient(headers=headers, timeout=10.0) as http_client:
        try:
            async with streamable_http_client(endpoint_url, http_client=http_client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
        except Exception as exc:
            raise ConnectorUnreachable(str(exc)) from exc

    return [{"name": t.name, "description": t.description} for t in result.tools]


def discover_tools(endpoint_url: str, credentials_encrypted: str | None) -> list[dict]:
    credentials = decrypt(credentials_encrypted) if credentials_encrypted else None
    return asyncio.run(_discover_tools_async(endpoint_url, credentials))
