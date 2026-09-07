"""Show that the model has no memory of its own between requests.

The same two turns are sent twice, and the two runs are printed side by side:

1. Without history - each prompt is sent on its own, so when asked "What is my
    name?" the assistant has never seen the name and cannot answer.
2. With history - the first prompt, the assistant's reply, and the second
    prompt are sent together in one messages list, so the answer is there.
"""

import json, urllib.request
BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
SYSTEM = "Use English for the conversation."
CHAT_ENDPOINT = BASE + "/chat/completions"

def role_system(content):
    return {"role": "system", "content": content}

def role_user(content):
    return {"role": "user", "content": content}

def role_assistant(content):
    return {"role": "assistant", "content": content}

def chat(messages):
    body = json.dumps({"model": MODEL, "temperature": 0, "reasoning_effort": "none",
                       "messages": messages}).encode()
    req = urllib.request.Request(CHAT_ENDPOINT, data=body, headers=HEAD)
    with urllib.request.urlopen(req) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

first_prompt = "My name is David."
second_prompt = "What is my name?"
first_reply  = chat([role_system(SYSTEM), role_user(first_prompt)])
second_reply = chat([role_system(SYSTEM), role_user(second_prompt)])
print("[No Memory][1st]", "\n User: ",first_prompt, "\n Assistant: ", first_reply)
print("[No Memory][2nd]", "\n User: ",second_prompt, "\n Assistant: ", second_reply)

memory_reply = chat([role_system(SYSTEM),
                    role_user(first_prompt),
                    role_assistant(first_reply),
                    role_user(second_prompt)])
print("[Memory][1st]", "\n User: ",first_prompt, "\n Assistant: ", first_reply)
print("[Memory][2nd]", "\n User: ",second_prompt, "\n Assistant: ", memory_reply)
