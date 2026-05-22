from typing import Any, Protocol


class LLMProvider(Protocol):
    async def chat_completion(
        self, messages: list[dict[str, str]], schema: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...
    async def streaming_completion(
        self, messages: list[dict[str, str]]
    ) -> None: ...
