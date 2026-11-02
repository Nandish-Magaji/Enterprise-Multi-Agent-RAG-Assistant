from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlparse

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)
URL_PATTERN = re.compile(r"https?://[^\s)\]>]+")


def get_tavily_toolset() -> Any | None:
    """Build the ADK MCP toolset for Tavily when web search is configured."""
    if not settings.TAVILY_API_KEY:
        logger.info("Tavily MCP is disabled because TAVILY_API_KEY is not configured.")
        return None

    # from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams


    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=settings.TAVILY_MCP_URL,
            headers={
                "Authorization": f"Bearer {settings.TAVILY_API_KEY}",
                "Accept": "application/json, text/event-stream",
            },
        )
    )


def extract_tavily_sources(research_notes: str) -> list[dict[str, str]]:
    """Extract URLs explicitly returned by the Researcher as web citations."""
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_url in URL_PATTERN.findall(research_notes):
        url = raw_url.rstrip(".,;:")
        if url in seen:
            continue
        seen.add(url)
        parsed = urlparse(url)
        source_id = "web-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        sources.append(
            {
                "source_id": source_id,
                "source_title": parsed.netloc or url,
                "citation": url,
                "url": url,
                "source_type": "tavily_web",
            }
        )
    return sources


def build_tavily_context(sources: list[dict[str, str]]) -> str:
    if not sources:
        return ""
    return "\n\n".join(
        f"[Web Source: {source['citation']}]\n"
        "This URL was returned by the Tavily MCP search tool. "
        "Use it as a citation reference and do not invent unsupported details."
        for source in sources
    )
