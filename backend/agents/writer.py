from google.adk.agents import Agent
from config.prompt_loader import load_prompt
from config.settings import settings

writer = Agent(
    name="writer",
    model=settings.GEMINI_GENERATION_MODEL,
    instruction=load_prompt("writer.md"),
)
