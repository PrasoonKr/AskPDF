import requests
import json
import time

print("1. Logging in as dev user...")
res = requests.post("http://localhost:8000/auth/dev-login")
token = res.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

print("2. Creating session...")
res = requests.post("http://localhost:8000/sessions", headers=headers)
session_id = res.json()["session_id"]
print(f"Session ID: {session_id}")

q = "what is normalization and different types of normalization"
print(f"3. Sending query to /chat/stream: '{q}'")

t0 = time.time()
response = requests.post(
    "http://localhost:8000/chat/stream",
    headers=headers,
    json={"session_id": session_id, "question": q},
    stream=True,
    timeout=120,
)

sources = []
tokens = []
first_token_time = None

for line in response.iter_lines():
    if not line:
        continue
    line_str = line.decode("utf-8")
    if line_str.startswith("data: "):
        data_json = line_str[6:]
        try:
            data = json.loads(data_json)
            if isinstance(data, list):
                sources = data
                print(f"  [Sources Received in {time.time() - t0:.2f}s]: {[s['source'] + ' p.' + str(s['page']) for s in sources]}")
            elif "token" in data:
                if first_token_time is None:
                    first_token_time = time.time() - t0
                    print(f"  [First Token in {first_token_time:.2f}s]")
                tokens.append(data["token"])
            elif "answer" in data:
                print(f"  [Stream Done in {time.time() - t0:.2f}s]")
        except Exception:
            pass

full_text = "".join(tokens)
print("\n--- FINAL ANSWER SNIPPET ---")
print(full_text[:400])
print("\n--- SOURCES ---")
for s in sources:
    print(f"- {s['source']} (Page {s['page']}, Score: {s.get('score')})")
