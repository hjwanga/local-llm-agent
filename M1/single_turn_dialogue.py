"""Ask the local model a single question, with the request split into helpers.

Same one-shot exchange as api_test_chat_completions.py, but the call is broken
into the four steps every later script reuses:

1. build_body(prompt) - wrap the system rule and the user turn into a JSON body.
2. send(body)         - POST the body and return the decoded response.
3. reply(data)        - pull choices[0].message.content out of the response.
4. chat(prompt)       - chain the three above into one call.

No history is kept, so each chat() call starts from an empty conversation.
"""

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