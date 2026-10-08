import os
import traceback
from openai import OpenAI

# The OpenAI client automatically picks up OPENAI_API_KEY and OPENAI_BASE_URL from the environment
client = OpenAI()

try:
    # Note: The standard endpoint for chat models is chat.completions
    response = client.chat.completions.create(
        model="openai.gpt-oss-120b",
        messages=[
            {"role": "user", "content": "Say hello in one sentence."}
        ]
    )
    print("SUCCESS:")
    print(response.choices[0].message.content)
except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR:", e)
    if hasattr(e, 'body'):
        print("BODY:", e.body)
    if hasattr(e, 'response'):
        print("RESPONSE:", e.response)
