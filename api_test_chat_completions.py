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