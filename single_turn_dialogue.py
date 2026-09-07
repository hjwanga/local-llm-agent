import json, urllib.request
BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
CHAT_ENDPOINT = BASE + "/chat/completions"

def build_body(prompt):
    payload = {"model": MODEL, "temperature": 0, "reasoning_effort": "none",
               "messages": [
                   {"role": "system", "content": "Use English for the conversation."},
                   {"role": "user", "content": prompt}]}
    return json.dumps(payload).encode()

def send(body):
    req = urllib.request.Request(CHAT_ENDPOINT, data=body, headers=HEAD)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def reply(data):
    return data["choices"][0]["message"]["content"].strip()

def chat(prompt):
    return reply(send(build_body(prompt)))

first_prompt = "Hello, my name is David."
first_reply  = chat(first_prompt)
print("User:", first_prompt)
print("Assistant:", first_reply)