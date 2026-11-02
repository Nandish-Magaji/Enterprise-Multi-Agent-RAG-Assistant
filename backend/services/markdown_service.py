from __future__ import annotations

from typing import Any


def render_markdown(
    title: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
) -> str:
    """Return a portable Markdown document with optional source citations."""
    document = content.strip()
    if not document:
        raise ValueError("Cannot export an empty document.")
    if not document.startswith("#"):
        document = f"# {title.strip() or 'Generated document'}\n\n{document}"

    source_lines = []
    for source in sources or []:
        citation = source.get("citation")
        if citation:
            source_lines.append(f"- {citation}")
    if source_lines and "\n## Sources\n" not in f"\n{document}\n":
        source_block = "\n".join(source_lines)
        document = f"{document.rstrip()}\n\n## Sources\n\n{source_block}\n"
    return document
