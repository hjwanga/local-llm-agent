import json, urllib.request, urllib.error, os
BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
CHAT_ENDPOINT = BASE + "/chat/completions"
FILE = "multi_turn_dialogue.json"

def build_body(messages):
    payload = {"model": MODEL, "temperature": 0, "reasoning_effort": "none",
               "messages": [{"role": "system", "content": "Use English for the conversation."}] + messages}
    return json.dumps(payload).encode()

def send(body):
    req = urllib.request.Request(CHAT_ENDPOINT, data=body, headers=HEAD)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def reply(data):
    return data["choices"][0]["message"]["content"].strip()

def chat(messages):
    return reply(send(build_body(messages)))

def load():
    if not os.path.exists(FILE):
        return []
    with open(FILE, encoding="utf-8") as f:
        return json.load(f)

def save(messages):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

messages = load()
print("Loaded", len(messages), "previous messages (type exit or quit to end)")
try:
    while True:
        user = input("You: ")
        if user in ("exit", "quit"):
            break
        if not user.strip():
            continue
        messages.append({"role": "user", "content": user})
        try:
            response = chat(messages)
        except (urllib.error.URLError, KeyError, ValueError) as e:
            messages.pop()
            print("Call failed: ", e)
            print("Check if LM Studio server is running and MODEL name is correct.")
            continue
        messages.append({"role": "assistant", "content": response})
        print("Assistant: ", response)
except (KeyboardInterrupt, EOFError):
    print()
finally:
    save(messages)
    print("Saved", len(messages), "messages to", FILE)
