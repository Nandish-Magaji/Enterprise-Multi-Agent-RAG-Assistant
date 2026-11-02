from __future__ import annotations

import io
import re
from typing import Any

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from services.markdown_service import render_markdown


def render_pdf(
    title: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
) -> bytes:
    """Render generated Markdown into a readable PDF document."""
    markdown = render_markdown(title, content, sources)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DocumentTitle", parent=styles["Title"], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="CodeBlock", parent=styles["Code"], fontName="Courier"))

    story = []
    for block in re.split(r"\n\s*\n", markdown):
        block = block.strip()
        if not block:
            continue
        if block.startswith("### "):
            story.append(Paragraph(_escape(block[4:]), styles["Heading3"]))
        elif block.startswith("## "):
            story.append(Paragraph(_escape(block[3:]), styles["Heading2"]))
        elif block.startswith("# "):
            story.append(Paragraph(_escape(block[2:]), styles["DocumentTitle"]))
        elif block.startswith("- "):
            for item in block.splitlines():
                story.append(Paragraph(f"• {_escape(item[2:])}", styles["BodyText"]))
        elif block.startswith("```"):
            code = block.strip("`").strip()
            story.append(Paragraph(_escape(code).replace("\n", "<br/>"), styles["CodeBlock"]))
        else:
            story.append(Paragraph(_escape(block).replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 0.12 * inch))

    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=LETTER,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=title,
    )
    document.build(story)
    return output.getvalue()


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
