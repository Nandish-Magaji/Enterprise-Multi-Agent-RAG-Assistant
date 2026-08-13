from adk.runner import runner
from adk.registry import AgentRegistry
from prompts.prompt_builder import PromptBuilder
from adk.sessions import session_manager
from google.genai import types


class AgentExecutor:

    def execute(
        self,
        agent_name: str,
        inputs: dict,
        json_output: bool = False,
    ) -> str:
        # Create the ADK Runner.
        adk_runner = runner.create_runner(agent_name)
        session = session_manager.create_session()
        prompt = PromptBuilder.build(
            agent_name,
            inputs,
        )
        message = types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=prompt
                )
            ],
        )
        events = adk_runner.run(
            user_id=session.user_id,
            session_id=session.id,
            new_message=message,
        )

        final_response = ""

        for event in events:

            # Skip events without content.
            if event.content is None:
                continue
            # Ignore user echoes.
            if event.author == "user":
                continue
            # Extract text parts.
            if event.content.parts:

                for part in event.content.parts:

                    if getattr(part, "text", None):

                        final_response += part.text

        # Return the agent response.
        return final_response.strip()
    

executor = AgentExecutor()