import time

from pydantic_ai.exceptions import (
    ModelConnectionError,
    ModelRateLimitError,
    ModelRequestRejectedError,
    ModelServerError,
    ModelTimeoutError,
    UnexpectedModelBehavior,
)

# Errors that usually disappear on the next try (Groq free tier: 429s, malformed tool calls).
RETRYABLE = (
    ModelRateLimitError,
    ModelRequestRejectedError,
    ModelServerError,
    ModelTimeoutError,
    ModelConnectionError,
    UnexpectedModelBehavior,
)


def with_retries(call, attempts: int = 3, wait: float = 8):
    for attempt in range(attempts):
        try:
            return call()
        except RETRYABLE:
            if attempt == attempts - 1:
                raise
            time.sleep(wait)
