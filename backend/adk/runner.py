from google.adk.runners import Runner

from adk.registry import AgentRegistry
from adk.sessions import session_manager


class ADKRunner:

    APP_NAME = "enterprise_multi_agent_rag"

    def create_runner(
        self,
        agent_name: str,
    ):

        agent = AgentRegistry.get(agent_name)

        return Runner(
            agent=agent,
            app_name=self.APP_NAME,
            session_service=session_manager.service,
        )


runner = ADKRunner()