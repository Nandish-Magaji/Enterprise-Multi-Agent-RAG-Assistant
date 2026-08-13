from dotenv import load_dotenv

import os

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:

    APP_NAME = "Enterprise Multi-Agent RAG Assistant"

    GOOGLE_API_KEY = os.getenv(
        "GOOGLE_API_KEY"
    )

    GENERATION_MODEL = os.getenv(
        "GEMINI_GENERATION_MODEL",
        "gemini-2.5-flash",
    )

    EMBEDDING_MODEL = os.getenv(
        "GEMINI_EMBEDDING_MODEL",
        "gemini-embedding-001",
    )

    DEFAULT_TOP_K = 6

    MAX_RETRIES = 3

    RETRY_DELAY_SECONDS = 2

    TEMPERATURE = 0.2


settings = Settings()