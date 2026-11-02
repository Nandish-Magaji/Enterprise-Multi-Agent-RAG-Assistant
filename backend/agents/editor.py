from google.adk.agents import Agent
from config.prompt_loader import load_prompt
from config.settings import settings

editor = Agent(
    name="editor",
    model=settings.GEMINI_GENERATION_MODEL,
    instruction=load_prompt("editor.md"),
)
