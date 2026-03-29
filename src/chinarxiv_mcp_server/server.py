"""ChinaRxiv MCP Server — search and read translated Chinese preprints."""

import logging
from typing import Any, Dict, List

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from .config import Settings
from .tools import (
    download_tool,
    handle_download,
    handle_list_papers,
    handle_read_paper,
    handle_search,
    list_tool,
    read_tool,
    search_tool,
)

settings = Settings()
logger = logging.getLogger("chinarxiv-mcp-server")
logger.setLevel(logging.INFO)
server = Server(settings.APP_NAME)


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available ChinaRxiv research tools."""
    return [search_tool, download_tool, list_tool, read_tool]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for ChinaRxiv research functionality."""
    logger.debug(f"Calling tool {name} with arguments {arguments}")
    try:
        if name == "search_papers":
            return await handle_search(arguments)
        elif name == "download_paper":
            return await handle_download(arguments)
        elif name == "list_papers":
            return await handle_list_papers(arguments)
        elif name == "read_paper":
            return await handle_read_paper(arguments)
        else:
            return [types.TextContent(type="text", text=f"Error: Unknown tool {name}")]
    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the server async context."""
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name=settings.APP_NAME,
                server_version=settings.APP_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )
