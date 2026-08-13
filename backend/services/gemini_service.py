"""
Gemini Service

Centralized interface for interacting with
Google Gemini models.

Responsibilities:
- Text Generation
- JSON Generation
- Embedding Generation
- Automatic Retry
"""

from __future__ import annotations

import time
from typing import Any, Callable

from google import genai
from google.genai import types

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# Gemini Client (Singleton)
# ------------------------------------------------------------------

client = genai.Client(
    api_key=settings.GOOGLE_API_KEY
)


# ------------------------------------------------------------------
# Text Generation
# ------------------------------------------------------------------

def generate_response(prompt: str) -> str:
    """
    Generate a natural language response.
    """
    logger.info(
    "Generating text response..."
    )
    response = _retry(
        lambda: client.models.generate_content(
            model=settings.GENERATION_MODEL,
            contents=prompt,
        )
    )
    logger.info(
    "Response generated successfully."
    )

    return response.text.strip()


# ------------------------------------------------------------------
# JSON Generation
# ------------------------------------------------------------------

def generate_json(prompt: str) -> str:
    """
    Generate structured JSON.
    """
    logger.info(
    "Generating text response..."
    )
    response = _retry(
        lambda: client.models.generate_content(
            model=settings.GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=settings.TEMPERATURE,
            ),
        )
    )
    logger.info(
    "Response generated successfully."
    )
    return response.text.strip()


# ------------------------------------------------------------------
# Embedding Generation
# ------------------------------------------------------------------

def embed_text(text: str) -> list[float]:
    """
    Generate embedding for a single text.
    """
    logger.info(
    "Generating embedding for a single text..."
    )
    logger.info(
    "Embedding generated for a single text successfully."
    )

    return embed_texts([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.
    """
    logger.info(
    "Generating embeddings for multiple texts..."
    )
    response = _retry(
        lambda: client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
            ),
        )
    )
    logger.info(
    "Embeddings generated for multiple texts successfully."
    )
    return [embedding.values for embedding in response.embeddings]


# ------------------------------------------------------------------
# Retry Utility
# ------------------------------------------------------------------

def _retry(
    operation: Callable[[], Any],
) -> Any:
    """
    Retry Gemini requests using exponential backoff.
    """

    last_error = None

    for attempt in range(settings.MAX_RETRIES):

        try:
            return operation()

        except Exception as exc:

            last_error = exc

            if attempt == settings.MAX_RETRIES - 1:
                break

            time.sleep(
                settings.RETRY_DELAY_SECONDS * (attempt + 1)
            )

    raise last_error