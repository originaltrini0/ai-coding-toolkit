"""
Plaid MCP Server Implementation.

This module implements a Model Context Protocol (MCP) server for Plaid API integration.
It uses a robust detection mechanism to support both MCP 1.x (decorator API) and MCP 2.x
(callback API).

Feature Detection Strategy:
  - Checks for Server.list_tools decorator (MCP 1.x only)
  - If absent, uses Server on_list_tools/on_call_tool callbacks (MCP 2.x)
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List

import click
import mcp.server.stdio
import mcp.types as types
import plaid
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server import Server as _PlaidServer  # Server may be legacy or lowlevel
from plaid.api import plaid_api

from mcp_server_plaid.clients.bill import AskBillClient
from mcp_server_plaid.tools import register_all_tools

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("plaid-mcp-server")

# Constants
__version__ = "0.1.0"
REQUEST_TIMEOUT = 30.0


# ── Robust Feature Detection ─────────────────────────────────────────

# Use method-level detection (hasattr).
# Server.list_tools exists as a decorator in MCP 1.x, but is removed
# in MCP 2.x (replaced by on_list_tools/on_call_tool callback params).
_HAS_DECORATOR_API = hasattr(_PlaidServer, "list_tools")

# ── Helper: Build Plaid clients (shared between API versions) ──────────

def _make_clients(client_id, secret, enabled_categories):
    """Create shared Plaid and Bill clients with tool registry."""
    # Plaid client
    configuration = plaid.Configuration(
        host=plaid.Environment.Sandbox,
        api_key={
            "clientId": client_id,
            "secret": secret,
        },
    )
    plaid_client = plaid_api.PlaidApi(plaid.ApiClient(configuration))

    # Bill client (AskBill WebSocket)
    ask_bill_client = AskBillClient("wss://hello-finn.herokuapp.com/")

    # Tool registry (only created once, cached by singleton)
    tool_registry = register_all_tools(enabled_categories)

    return plaid_client, ask_bill_client, tool_registry


# ── MCP 2.x (callback) Server ─────────────────────────────────────────

def _build_new_api_server(client_id, secret, enabled_categories):
    """Create server for MCP 2.x using lowlevel callback API."""
    plaid_client, ask_bill_client, tool_registry = _make_clients(
        client_id, secret, enabled_categories
    )

    def _make_on_list_tools():
        async def on_list_tools(ctx, params):
            return types.ListToolsResult(tools=tool_registry.get_tools())
        return on_list_tools

    def _make_on_call_tool():
        async def on_call_tool(ctx, params):
            name = params.name
            arguments = params.arguments or {}

            if not tool_registry.has_tool(name):
                raise ValueError(f"Unknown tool: {name}")

            handler = tool_registry.get_handler(name)
            if handler is None:
                raise ValueError(f"No handler registered for tool: {name}")

            result = await handler(
                arguments,
                bill_client=ask_bill_client,
                plaid_client=plaid_client,
            )
            return types.CallToolResult(content=result, is_error=False)

        return on_call_tool

    # In MCP 2.x, Server is lowlevel.Server with on_list_tools/on_call_tool params
    server = _PlaidServer(
        "plaid",
        on_list_tools=_make_on_list_tools(),
        on_call_tool=_make_on_call_tool(),
    )
    return server


# ── MCP 1.x (decorator) Server ────────────────────────────────────────

def _build_old_api_server(client_id, secret, enabled_categories):
    """Create server for MCP 1.x using legacy decorator API."""
    plaid_client, ask_bill_client, tool_registry = _make_clients(
        client_id, secret, enabled_categories
    )

    server = _PlaidServer("plaid")

    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        return tool_registry.get_tools()

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict[str, Any] | None
    ) -> List[types.TextContent]:
        if not tool_registry.has_tool(name):
            raise ValueError(f"Unknown tool: {name}")

        handler = tool_registry.get_handler(name)
        if handler is None:
            raise ValueError(f"No handler registered for tool: {name}")

        return await handler(
            arguments or {},
            bill_client=ask_bill_client,
            plaid_client=plaid_client,
        )

    return server


# ── Common server builder ─────────────────────────────────────────────

def serve(client_id: str, secret: str, enabled_categories: str):
    """
    Initialize and configure the MCP server with Plaid tools.

    Automatically detects MCP version (1.x vs 2.x) and returns
    the appropriate server implementation.
    """
    if _HAS_DECORATOR_API:
        return _build_old_api_server(client_id, secret, enabled_categories)
    else:
        return _build_new_api_server(client_id, secret, enabled_categories)


# ── Main (runs the server after initialisation) ──────────────────────

@click.command()
@click.option("--client-id", type=str, help="Plaid client ID", envvar="PLAID_CLIENT_ID", required=True)
@click.option("--secret", type=str, help="Plaid secret", envvar="PLAID_SECRET", required=True)
@click.option("--enabled-categories", type=str, help="Comma-separated list of enabled categories",
              envvar="TOOLS_TO_ENABLE")
def main(client_id: str, secret: str, enabled_categories: str):
    """Entry point for the MCP server."""
    logger.info("Using MCP API: %s", "new (callbacks)" if not _HAS_DECORATOR_API else "old (decorators)")

    if not client_id or not secret:
        logger.error(
            "PLAID_CLIENT_ID and PLAID_SECRET environment variables must be set"
        )
        sys.exit(1)

    async def _run():
        logger.info("Setting up stdio communication channels")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            server = serve(client_id, secret, enabled_categories)

            if _HAS_DECORATOR_API:
                # MCP 1.x: use get_capabilities + InitializationOptions manually
                init_options = InitializationOptions(
                    server_name="plaid",
                    server_version=__version__,
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                )
            else:
                # MCP 2.x: use create_initialization_options()
                init_options = server.create_initialization_options()

            await server.run(read_stream, write_stream, init_options)

    asyncio.run(_run())
