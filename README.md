# chinarxiv-mcp-server

An MCP (Model Context Protocol) server that provides AI assistants with access to machine-translated Chinese preprints from [ChinaRxiv](https://chinarxiv.org) and other Chinese academic repositories.

Search, download, and read translated Chinese research papers directly from your AI assistant.

## Tools

| Tool | Description |
|------|-------------|
| `search_papers` | Search for translated Chinese preprints by query, author, subject, date range, etc. |
| `download_paper` | Download a paper's translated full text (markdown), figures, and optional PDF |
| `list_papers` | List all papers downloaded to local storage |
| `read_paper` | Read the full content of a downloaded paper |

## Installation

### Claude Desktop / Claude Code

Add to your MCP config (`claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "chinarxiv": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/olety/chinarxiv-mcp-server.git", "chinarxiv-mcp-server"]
    }
  }
}
```

### From source

```bash
git clone https://github.com/olety/chinarxiv-mcp-server.git
cd chinarxiv-mcp-server

# Using uv (recommended)
uv venv && source .venv/bin/activate
uv pip install -e .

# Or using pip
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Then add to your MCP config:

```json
{
  "mcpServers": {
    "chinarxiv": {
      "command": "/path/to/chinarxiv-mcp-server/.venv/bin/chinarxiv-mcp-server"
    }
  }
}
```

## Usage

### Search for papers

```
search_papers(query="quantum computing", max_results=5)
search_papers(query="Li Wei", search_field="author", subject="physics")
search_papers(query="CRISPR", from_date="2025-01-01", has_full_text=true)
```

### Download and read

```
download_paper(paper_id="chinaxiv-202603.00088", include_figures=true)
read_paper(paper_id="chinaxiv-202603.00088")
list_papers()
```

## Configuration

Environment variables (prefix with `CHINARXIV_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `CHINARXIV_API_EMAIL` | — | Email for API identification |
| `CHINARXIV_MAX_RESULTS` | `100` | Maximum search results |
| `CHINARXIV_REQUEST_TIMEOUT` | `30` | HTTP timeout in seconds |

Storage path can also be set via CLI:

```bash
chinarxiv-mcp-server --storage-path /path/to/papers
```

Default storage: `~/.chinarxiv-mcp-server/papers`

## Requirements

- Python >= 3.11

## License

MIT
