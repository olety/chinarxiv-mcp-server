"""Search functionality for the ChinaRxiv MCP server."""

import json
import logging
from typing import Any, Dict, List

import mcp.types as types

from ..config import Settings, get_api_client

logger = logging.getLogger("chinarxiv-mcp-server")
settings = Settings()

search_tool = types.Tool(
    name="search_papers",
    description=(
        "Search for translated Chinese preprints on ChinaRxiv. "
        "Supports full-text search across titles, abstracts, and authors. "
        "Returns paper metadata including IDs needed for download_paper. "
        "Papers are machine-translated from ChinaXiv and other Chinese repositories."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (searches title, abstract, authors)",
            },
            "search_field": {
                "type": "string",
                "enum": ["title", "author", "abstract"],
                "description": "Limit search to a specific field. Omit to search all fields.",
            },
            "subject": {
                "type": "string",
                "description": "Filter by subject category",
            },
            "from_date": {
                "type": "string",
                "description": "Papers published on or after this date (YYYY-MM-DD)",
            },
            "to_date": {
                "type": "string",
                "description": "Papers published on or before this date (YYYY-MM-DD)",
            },
            "has_full_text": {
                "type": "boolean",
                "description": "Only return papers with full text available",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return (1-100, default 20)",
            },
        },
        "required": ["query"],
    },
)


async def handle_search(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper search requests."""
    try:
        params: Dict[str, Any] = {"q": arguments["query"]}

        if field := arguments.get("search_field"):
            params["search_field"] = field
        if subject := arguments.get("subject"):
            params["subject"] = subject
        if from_date := arguments.get("from_date"):
            params["from_date"] = from_date
        if to_date := arguments.get("to_date"):
            params["to_date"] = to_date
        if arguments.get("has_full_text"):
            params["has_full_text"] = "true"

        limit = min(int(arguments.get("max_results", 20)), settings.MAX_RESULTS)
        params["limit"] = limit

        async with get_api_client() as client:
            resp = await client.get("/api/v1/papers", params=params)
            resp.raise_for_status()
            data = resp.json()

        papers = []
        for p in data.get("data", []):
            papers.append({
                "id": p["id"],
                "title": p.get("title", ""),
                "authors": p.get("authors", []),
                "abstract": p.get("abstract", ""),
                "date": p.get("date", ""),
                "subjects": p.get("subjects", []),
                "has_full_text": p.get("has_full_text", False),
                "has_figures": p.get("has_figures", False),
                "has_pdf": p.get("has_pdf", False),
                "source_url": p.get("source_url", ""),
            })

        response = {
            "total_results": data.get("total", 0),
            "returned": len(papers),
            "next_cursor": data.get("next_cursor"),
            "papers": papers,
        }
        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        logger.error(f"Search error: {e}")
        return [types.TextContent(type="text", text=f"Error searching papers: {e}")]
