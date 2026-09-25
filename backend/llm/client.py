from ollama import chat

from backend.config import LLMConfig


class OllamaClient:
    """
    Low-level client responsible for communicating with Ollama.
    """

    def warmup(self) -> None:
        """
        Preloads the model into memory so the user's first query has zero cold-start delay.
        """
        try:
            chat(
                model=LLMConfig.MODEL,
                messages=[{"role": "user", "content": "ping"}],
                options={
                    "temperature": LLMConfig.TEMPERATURE,
                    "num_ctx": LLMConfig.NUM_CTX,
                },
                keep_alive=-1,
            )
        except Exception as e:
            print(f"Ollama warmup warning: {e}")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = chat(
            model=LLMConfig.MODEL,
            messages=messages,
            options={
                "temperature": LLMConfig.TEMPERATURE,
                "num_ctx": LLMConfig.NUM_CTX,
            },
            keep_alive=-1,
        )

        return response["message"]["content"]

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ):
        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = chat(
            model=LLMConfig.MODEL,
            messages=messages,
            options={
                "temperature": LLMConfig.TEMPERATURE,
                "num_ctx": LLMConfig.NUM_CTX,
            },
            keep_alive=-1,
            stream=True,
        )


        for chunk in response:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content