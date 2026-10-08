import os
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv("backend/.env")
client = OpenAI()

try:
    print("Testing client.responses...")
    stream = client.responses.create(
        model="openai.gpt-oss-120b",
        input=[
            {"role": "user", "content": "Tell me a short story about a robot."}
        ],
        stream=True
    )
    for event in stream:
        print(event)
    print("SUCCESS!")
except Exception as e:
    import traceback
    traceback.print_exc()
