from google.adk.agents import Agent
from config.prompt_loader import load_prompt
from config.settings import settings
from tools.tavily_mcp import get_tavily_toolset


tavily_toolset = get_tavily_toolset()
researcher_tools = [tavily_toolset] if tavily_toolset else []

researcher = Agent(
    name="researcher",
    model=settings.GEMINI_GENERATION_MODEL,
    instruction=load_prompt("researcher.md"),
    tools=researcher_tools,
)
