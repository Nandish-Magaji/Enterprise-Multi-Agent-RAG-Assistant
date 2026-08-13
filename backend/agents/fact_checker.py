from google.adk.agents import Agent
from config.prompt_loader import load_prompt

fact_checker = Agent(
    name="fact_checker",
    model="gemini-2.5-flash",
    instruction=load_prompt("fact_checker.md"),
)