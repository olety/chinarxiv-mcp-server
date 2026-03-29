"""Read functionality for the ChinaRxiv MCP server."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import mcp.types as types

from ..config import Settings

logger = logging.getLogger("chinarxiv-mcp-server")
settings = Settings()

read_tool = types.Tool(
    name="read_paper",
    description="Read the full content of a downloaded ChinaRxiv paper in markdown format",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "The ChinaRxiv paper ID to read (e.g., chinaxiv-202603.00088)",
            },
        },
        "required": ["paper_id"],
    },
)


async def handle_read_paper(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle requests to read a paper's content."""
    try:
        paper_id = arguments["paper_id"]
        md_path = Path(settings.STORAGE_PATH) / f"{paper_id}.md"

        if not md_path.exists():
            return [types.TextContent(type="text", text=json.dumps({
                "status": "error",
                "message": f"Paper {paper_id} not found in storage. Use download_paper first.",
            }))]

        content = md_path.read_text(encoding="utf-8")
        return [types.TextContent(type="text", text=json.dumps({
            "status": "success",
            "paper_id": paper_id,
            "content": content,
        }))]

    except Exception as e:
        logger.error(f"Read error: {e}")
        return [types.TextContent(type="text", text=f"Error reading paper: {e}")]
