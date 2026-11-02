from tools.tavily_mcp import build_tavily_context, extract_tavily_sources


def test_extract_tavily_sources_deduplicates_urls_and_preserves_citations():
    sources = extract_tavily_sources(
        "Web Sources:\n- https://example.com/article.\n- https://example.com/article"
    )

    assert len(sources) == 1
    assert sources[0]["citation"] == "https://example.com/article"
    assert sources[0]["source_type"] == "tavily_web"
    assert "Tavily MCP" in build_tavily_context(sources)
