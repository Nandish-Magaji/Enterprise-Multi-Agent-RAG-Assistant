from google.adk.agents import Agent
from config.prompt_loader import load_prompt

researcher = Agent(
    name="researcher",
    model="gemini-2.5-flash",
    instruction=load_prompt("researcher.md"),
)