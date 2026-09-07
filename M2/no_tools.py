"""Show what a model answers with no tools available - the baseline for M2.

The model is asked "What time is it now?" and has no way to find out: it holds
no clock, so it either guesses, hallucinates a time, or explains that it cannot
know. Nothing here parses or executes anything.

has_tools.py answers the same question by handing the model a tool it can call.
"""

import json, urllib.request
BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
CHAT_ENDPOINT = BASE + "/chat/completions"
QUESTION = "What time is it now?"
SYSTEM = "Use English for the conversation."

def chat(messages):
    body = json.dumps({"model": MODEL, "temperature": 0, "reasoning_effort": "none",
                       "messages": messages}).encode()
    req = urllib.request.Request(CHAT_ENDPOINT,
                                 data=body, headers=HEAD)
    with urllib.request.urlopen(req) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

print(chat([{"role": "system", "content": SYSTEM},
            {"role": "user", "content": QUESTION}]))