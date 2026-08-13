from google.adk.agents import Agent
from config.prompt_loader import load_prompt

editor = Agent(
    name="editor",
    model="gemini-2.5-flash",
    instruction=load_prompt("editor.md"),
)