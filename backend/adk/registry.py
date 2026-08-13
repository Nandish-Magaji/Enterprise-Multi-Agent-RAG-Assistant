from adk.register_agents import REGISTERED_AGENTS


class AgentRegistry:

    @staticmethod
    def get(agent_name: str):

        agent = REGISTERED_AGENTS.get(agent_name)

        if agent is None:
            raise ValueError(
                f"Unknown agent '{agent_name}'."
            )

        return agent