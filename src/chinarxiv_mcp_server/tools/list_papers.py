"""List functionality for the ChinaRxiv MCP server."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.types as types

from ..config import Settings

logger = logging.getLogger("chinarxiv-mcp-server")
settings = Settings()

list_tool = types.Tool(
    name="list_papers",
    description="List all ChinaRxiv papers downloaded to local storage",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)


def _parse_header(md_path: Path) -> Dict[str, str]:
    """Parse metadata from the first few lines of a saved paper."""
    info: Dict[str, str] = {}
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 5:
                    break
                line = line.strip()
                if line.startswith("# "):
                    info["title"] = line[2:]
                elif line.startswith("**Authors:**"):
                    # Parse: **Authors:** X  |  **Published:** Y  |  **ID:** [Z](url)
                    for part in line.split("  |  "):
                        part = part.strip()
                        if part.startswith("**Authors:**"):
                            info["authors"] = part.replace("**Authors:**", "").strip()
                        elif part.startswith("**Published:**"):
                            info["published"] = part.replace("**Published:**", "").strip()
    except Exception:
        pass
    return info


async def handle_list_papers(
    arguments: Optional[Dict[str, Any]] = None,
) -> List[types.TextContent]:
    """Handle requests to list all stored papers."""
    try:
        storage = Path(settings.STORAGE_PATH)
        md_files = sorted(storage.glob("*.md"))

        papers = []
        for md_path in md_files:
            paper_id = md_path.stem
            header = _parse_header(md_path)
            papers.append({
                "paper_id": paper_id,
                "title": header.get("title", ""),
                "authors": header.get("authors", ""),
                "published": header.get("published", ""),
                "has_figures": (storage / paper_id).is_dir(),
                "has_pdf": (storage / f"{paper_id}.pdf").exists(),
            })

        response = {"total_papers": len(papers), "papers": papers}
        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        logger.error(f"List error: {e}")
        return [types.TextContent(type="text", text=f"Error listing papers: {e}")]
