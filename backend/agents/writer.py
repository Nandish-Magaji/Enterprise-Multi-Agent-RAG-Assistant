from google.adk.agents import Agent
from config.prompt_loader import load_prompt

writer = Agent(
    name="writer",
    model="gemini-2.5-flash",
    instruction=load_prompt("writer.md"),
)