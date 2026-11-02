from google.adk.agents import Agent
from config.prompt_loader import load_prompt
from config.settings import settings

fact_checker = Agent(
    name="fact_checker",
    model=settings.GEMINI_GENERATION_MODEL,
    instruction=load_prompt("fact_checker.md"),
)
