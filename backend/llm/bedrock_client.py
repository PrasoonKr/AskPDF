import json
import boto3

class BedrockLLMClient:
    """
    Client for generating text via AWS Bedrock using Meta Llama 3 or Anthropic Claude 3 Haiku.
    """
    def __init__(self, model_id="meta.llama3-8b-instruct-v1:0", region_name="us-east-1"):
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def warmup(self) -> None:
        pass

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        # Defaulting to Llama 3 payload format for Bedrock
        formatted_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_prompt or "You are a helpful assistant."}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        body = {
            "prompt": formatted_prompt,
            "max_gen_len": 1024,
            "temperature": 0.2,
            "top_p": 0.9
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('generation', '').strip()

    def generate_stream(self, prompt: str, system_prompt: str | None = None):
        # We can implement streaming similarly if needed, for now just yield full string
        yield self.generate(prompt, system_prompt)
