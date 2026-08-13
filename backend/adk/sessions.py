from google.adk.sessions import InMemorySessionService


class SessionManager:

    APP_NAME = "enterprise_multi_agent_rag"
    USER_ID = "default_user"

    def __init__(self):
        self._service = InMemorySessionService()

    @property
    def service(self):
        return self._service

    def create_session(self):

        session = self._service.create_session_sync(
            app_name=self.APP_NAME,
            user_id=self.USER_ID,
        )

        return session


session_manager = SessionManager()