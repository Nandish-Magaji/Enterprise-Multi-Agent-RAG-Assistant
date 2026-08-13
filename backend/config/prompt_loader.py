"""
Loads prompt files stored in agents/prompts.
"""

from pathlib import Path


PROMPT_DIR = (
    Path(__file__)
    .parent.parent
    / "agents"
    / "prompts"
)


def load_prompt(filename: str) -> str:

    path = PROMPT_DIR / filename

    return path.read_text(
        encoding="utf-8"
    ).strip()