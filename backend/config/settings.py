import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    """Validated application configuration sourced from environment variables."""

    APP_NAME: str = "Enterprise Multi-Agent RAG Assistant"

    GOOGLE_API_KEY: str | None = None
    GEMINI_GENERATION_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # External OIDC/JWT validation. No local credentials or token issuer is used.
    OIDC_ISSUER_URL: str | None = None
    OIDC_JWKS_URL: str | None = None
    OIDC_AUDIENCE: str | None = None
    OIDC_AUTHORIZATION_URL: str | None = None
    OIDC_TOKEN_URL: str | None = None
    OIDC_ROLE_CLAIM: str = "roles"
    OIDC_REVIEWER_ROLE: str = "reviewer"

    TAVILY_API_KEY: str | None = None
    TAVILY_MCP_URL: str = "https://mcp.tavily.com/mcp/"
    TAVILY_SEARCH_DEPTH: str = "basic"

    SQLITE_PATH: Path = BASE_DIR / "database" / "sqllite.db"
    CHROMA_PERSIST_DIRECTORY: Path = BASE_DIR / "database" / "chroma"
    CHROMA_COLLECTION_NAME: str = "rag_chunks"

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    DEFAULT_TOP_K: int = Field(default=6, ge=1, le=50)
    MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    RETRY_DELAY_SECONDS: float = Field(default=2, ge=0)
    TEMPERATURE: float = Field(default=0.2, ge=0, le=2)

    @field_validator(
        "GOOGLE_API_KEY",
        "OIDC_ISSUER_URL",
        "OIDC_JWKS_URL",
        "OIDC_AUDIENCE",
        "TAVILY_API_KEY",
        mode="before",
    )
    @classmethod
    def blank_values_are_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("SQLITE_PATH", "CHROMA_PERSIST_DIRECTORY", mode="before")
    @classmethod
    def resolve_storage_path(cls, value: object) -> object:
        if not isinstance(value, (str, Path)):
            return value
        path = Path(value)
        if path.is_absolute():
            return path
        project_root = BASE_DIR.parent
        if path.parts and path.parts[0] == BASE_DIR.name:
            return project_root / path
        return BASE_DIR / path

    @classmethod
    def from_environment(cls) -> "Settings":
        values: dict[str, object] = {}
        environment_names = {
            "GOOGLE_API_KEY": "GOOGLE_API_KEY",
            "GEMINI_GENERATION_MODEL": "GEMINI_GENERATION_MODEL",
            "GEMINI_EMBEDDING_MODEL": "GEMINI_EMBEDDING_MODEL",
            "OIDC_ISSUER_URL": "OIDC_ISSUER_URL",
            "OIDC_JWKS_URL": "OIDC_JWKS_URL",
            "OIDC_AUDIENCE": "OIDC_AUDIENCE",
            "OIDC_AUTHORIZATION_URL": "OIDC_AUTHORIZATION_URL",
            "OIDC_TOKEN_URL": "OIDC_TOKEN_URL",
            "OIDC_ROLE_CLAIM": "OIDC_ROLE_CLAIM",
            "OIDC_REVIEWER_ROLE": "OIDC_REVIEWER_ROLE",
            "TAVILY_API_KEY": "TAVILY_API_KEY",
            "TAVILY_MCP_URL": "TAVILY_MCP_URL",
            "TAVILY_SEARCH_DEPTH": "TAVILY_SEARCH_DEPTH",
            "SQLITE_PATH": "SQLITE_PATH",
            "CHROMA_PERSIST_DIRECTORY": "CHROMA_PERSIST_DIRECTORY",
            "CHROMA_COLLECTION_NAME": "CHROMA_COLLECTION_NAME",
            "CORS_ORIGINS": "CORS_ORIGINS",
            "DEFAULT_TOP_K": "DEFAULT_TOP_K",
            "MAX_RETRIES": "MAX_RETRIES",
            "RETRY_DELAY_SECONDS": "RETRY_DELAY_SECONDS",
            "TEMPERATURE": "TEMPERATURE",
        }
        for field_name, environment_name in environment_names.items():
            if environment_name in os.environ:
                values[field_name] = os.environ[environment_name]
        return cls(**values)


settings = Settings.from_environment()
