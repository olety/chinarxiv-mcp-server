"""Download functionality for the ChinaRxiv MCP server."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import aiofiles
import mcp.types as types

from ..config import Settings, get_api_client

B2_FIGURES_BASE = "https://f004.backblazeb2.com/file/chinaxiv"

logger = logging.getLogger("chinarxiv-mcp-server")
settings = Settings()

download_tool = types.Tool(
    name="download_paper",
    description=(
        "Download a ChinaRxiv paper for local reading. "
        "Saves the full translated text as markdown. "
        "By default also downloads translated figures if available. "
        "Optionally downloads the English PDF."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "ChinaRxiv paper ID (e.g., chinaxiv-202603.00088)",
            },
            "include_figures": {
                "type": "boolean",
                "description": "Download translated figure images (default: true)",
                "default": True,
            },
            "download_pdf": {
                "type": "boolean",
                "description": "Also download the English PDF if available (default: false)",
                "default": False,
            },
        },
        "required": ["paper_id"],
    },
)


def _paper_path(paper_id: str, suffix: str = ".md") -> Path:
    return Path(settings.STORAGE_PATH) / f"{paper_id}{suffix}"


def _figures_dir(paper_id: str) -> Path:
    return Path(settings.STORAGE_PATH) / paper_id


async def handle_download(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper download requests."""
    try:
        paper_id = arguments["paper_id"]
        include_figures = arguments.get("include_figures", True)
        download_pdf = arguments.get("download_pdf", False)
        md_path = _paper_path(paper_id)

        # Already downloaded
        if md_path.exists():
            return [types.TextContent(type="text", text=json.dumps({
                "status": "success",
                "message": "Paper already downloaded",
                "paper_id": paper_id,
                "storage_path": str(md_path),
            }))]

        async with get_api_client() as client:
            # Fetch metadata
            meta_resp = await client.get(f"/api/v1/papers/{paper_id}")
            meta_resp.raise_for_status()
            meta = meta_resp.json()

            # Fetch full text
            text_resp = await client.get(f"/api/v1/papers/{paper_id}/text")
            text_resp.raise_for_status()
            text_data = text_resp.json()

            body_md = text_data.get("body_md", "")
            word_count = text_data.get("word_count", 0)

            # Build markdown document
            title = meta.get("title", paper_id)
            authors = ", ".join(meta.get("authors", []))
            date = meta.get("date", "")
            source_url = meta.get("source_url", "")

            lines = [
                f"# {title}",
                "",
                f"**Authors:** {authors}  |  **Published:** {date}  |  **ID:** [{paper_id}]({source_url})",
                "",
                "---",
                "",
                body_md,
            ]

            # Download figures
            figure_count = 0
            if include_figures and meta.get("has_figures"):
                fig_resp = await client.get(f"/api/v1/papers/{paper_id}/figures")
                fig_resp.raise_for_status()
                fig_data = fig_resp.json()
                figures = fig_data.get("figures", [])

                if figures:
                    fig_dir = _figures_dir(paper_id)
                    fig_dir.mkdir(parents=True, exist_ok=True)

                    lines.extend(["", "---", "", "## Figures", ""])

                    for fig in figures:
                        raw_url = fig["url"]
                        fig_num = fig.get("number", str(figure_count + 1))
                        caption = fig.get("caption", "")

                        # API returns relative paths like "figures/chinaxiv-.../fig_4_en.png"
                        # Actual images are on B2: https://f004.backblazeb2.com/file/chinaxiv/...
                        if raw_url.startswith("http"):
                            fig_url = raw_url
                        else:
                            fig_url = f"{B2_FIGURES_BASE}/{raw_url}"

                        # Determine extension from URL
                        parsed = urlparse(fig_url)
                        ext = Path(parsed.path).suffix or ".png"
                        fig_filename = f"fig{fig_num}{ext}"
                        fig_path = fig_dir / fig_filename

                        try:
                            img_resp = await httpx.AsyncClient(timeout=30).get(fig_url)
                            img_resp.raise_for_status()
                            async with aiofiles.open(fig_path, "wb") as f:
                                await f.write(img_resp.content)
                            figure_count += 1

                            caption_text = f": {caption}" if caption else ""
                            lines.append(f"![Figure {fig_num}{caption_text}]({paper_id}/{fig_filename})")
                            lines.append("")
                        except Exception as e:
                            logger.warning(f"Failed to download figure {fig_num}: {e}")

            # Save markdown
            async with aiofiles.open(md_path, "w", encoding="utf-8") as f:
                await f.write("\n".join(lines))

            # Optional PDF download
            has_pdf = False
            if download_pdf and meta.get("has_pdf"):
                try:
                    pdf_resp = await client.get(
                        f"/api/v1/papers/{paper_id}/pdf",
                        follow_redirects=True,
                    )
                    pdf_resp.raise_for_status()
                    pdf_path = _paper_path(paper_id, ".pdf")
                    async with aiofiles.open(pdf_path, "wb") as f:
                        await f.write(pdf_resp.content)
                    has_pdf = True
                except Exception as e:
                    logger.warning(f"Failed to download PDF: {e}")

        return [types.TextContent(type="text", text=json.dumps({
            "status": "success",
            "message": f"Paper downloaded ({word_count} words, {figure_count} figures)",
            "paper_id": paper_id,
            "word_count": word_count,
            "figure_count": figure_count,
            "has_pdf": has_pdf,
            "storage_path": str(md_path),
        }))]

    except Exception as e:
        logger.error(f"Download error: {e}")
        return [types.TextContent(type="text", text=f"Error downloading paper: {e}")]
