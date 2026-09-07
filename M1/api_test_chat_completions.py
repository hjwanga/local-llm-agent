"""Send one chat completion request to a local LM Studio instance.

This is the smallest possible POST to /v1/chat/completions, written with the
standard library only so the request body and the response shape stay visible:

1. Build a messages list holding a system rule and a single user turn.
2. Encode it as JSON and POST it to the chat endpoint.
3. Print choices[0].message.content from the response.
"""

import json, urllib.request
BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
CHAT_ENDPOINT = BASE + "/chat/completions"

ask1  = [{"role": "system", "content": "Use English for the conversation."},
        {"role": "user", "content": "I am David"}]
body = json.dumps({"model": MODEL, "temperature": 0, "messages": ask1, "reasoning_effort": "none"}).encode()
req  = urllib.request.Request(CHAT_ENDPOINT, data=body, headers=HEAD)
with urllib.request.urlopen(req) as r:
    print(json.load(r)["choices"][0]["message"]["content"])