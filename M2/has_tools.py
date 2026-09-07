"""Demonstrate a basic tool-calling flow between a user and an assistant.

The conversation proceeds as follows:

1. User: What time is it now?
2. Assistant: TOOL_CALL: {"tool": "get_current_time", "args": {}}
3. The program parses the tool call, executes the tool, and sends the result
    back to the assistant.
4. User: Tool result: 12:34
5. Assistant: The current time is 12:34.
"""

import datetime, json, re, sys, urllib.request

BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
CHAT_ENDPOINT = BASE + "/chat/completions"
QUESTION = "What time is it now?"
SYSTEM = """
Use English for the conversation.
You can use the following tools:
- get_current_time(): Get the current time.
When you need to use a tool, output only one line, without any other text:
TOOL_CALL: {"tool": "tool_name", "args": {}}
"""

def chat(messages):
    body = json.dumps({"model": MODEL, "temperature": 0, "reasoning_effort": "none",
                       "messages": [{"role": "system", "content": SYSTEM}] + messages}).encode()
    req = urllib.request.Request(CHAT_ENDPOINT,
                                 data=body, headers=HEAD)
    with urllib.request.urlopen(req) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

def get_current_time():
    return datetime.datetime.now().strftime("%H:%M")

TOOLS = {"get_current_time": get_current_time}
TOOL_CALL_RE = re.compile(r'TOOL_CALL:\s*(\{.*\})')

def parse_tool_call(text):
    m = TOOL_CALL_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None

messages = [{"role": "user", "content": QUESTION}]
print(f"[User] {QUESTION}")

reply = chat(messages)
print(f"[Assistant] {reply}")

tool_call = parse_tool_call(reply)
if tool_call is None:
    print(reply)
    raise SystemExit
print(f"[User]  [Parsing] {tool_call['tool']}({tool_call['args']})")

tool_name = tool_call["tool"]
tool_args = tool_call["args"]
result = TOOLS[tool_name](**tool_args)
print(f"[User]  [Executing] Returned {result}")

handback = f"Tool result: {result}"
messages.append({"role": "assistant", "content": reply})
messages.append({"role": "user", "content": handback})
print(f"[User]  [Handback] send 「{handback}」back to message then asked assistant again.")

print(f"[Assistant] {chat(messages)}")

