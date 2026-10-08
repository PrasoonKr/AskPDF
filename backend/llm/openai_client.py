import os
from openai import OpenAI

class OpenAILLMClient:
    """
    Client for generating text via the OpenAI Python SDK (points to bedrock-mantle proxy).
    """
    def __init__(self, model_id="openai.gpt-oss-120b"):
        self.model_id = model_id
        # Client automatically picks up OPENAI_API_KEY and OPENAI_BASE_URL from the environment
        self.client = OpenAI()

    def warmup(self) -> None:
        pass

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})

        response = self.client.responses.create(
            model=self.model_id,
            input=messages
        )
        # Depending on exactly what responses.create returns, it could be an object or dictionary.
        # Assuming it behaves somewhat like completions or returns a raw dictionary if unsupported natively
        try:
            return response.choices[0].message.content.strip()
        except AttributeError:
            if hasattr(response, "output") and isinstance(response.output, list):
                # Try to find the output_text content
                for out in response.output:
                    # Depending on exactly what responses.create returns...
                    if hasattr(out, "type") and out.type == "message" and hasattr(out, "content"):
                        for block in out.content:
                            if hasattr(block, "text"):
                                return block.text
                    elif hasattr(out, "text"):
                        return out.text
            return str(response)

    def generate_stream(self, prompt: str, system_prompt: str | None = None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self.client.responses.create(
                model=self.model_id,
                input=messages,
                stream=True
            )
        except Exception as e:
            import traceback
            error_details = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_details += f" | Body: {e.response.text}"
            raise RuntimeError(f"OpenAI API Error: {error_details}")
        
        for event in stream:
            if hasattr(event, "type") and event.type == "response.output_text.delta":
                yield event.delta
