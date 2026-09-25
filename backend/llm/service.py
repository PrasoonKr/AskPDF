class LLMService:
    """
    Generic service for generating text using an LLM.
    """

    def __init__(self, client):
        self.client = client

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate text from a prompt.
        """

        response = self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        return response.strip()

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ):
        """
        Generate text stream from a prompt.
        """
        return self.client.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
        )