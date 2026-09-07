"""Answer the same question through the API's native tool-calling protocol,
run once per schema variant to see how much the tool's name and description
matter to the model's decision to call it.

The conversation proceeds as follows for each variant:

1. User: What time is it now?
2. Assistant: tool_calls: [{"id": "call_0", "function":
    {"name": "get_current_time", "arguments": "{}"}}]
3. The program looks the name up, executes the tool, and appends the result as
    a message of its own, a third role the hand-rolled version does not have:
    {"role": "tool", "tool_call_id": "call_0", "content": "12:34"}
4. Tool: 12:34
5. Assistant: The current time is 12:34.

VARIANTS swaps the schema's name and/or description for gibberish, one at a
time, to isolate which field the model actually leans on. If the assistant
never emits tool_calls for a variant, the model gave up trying to match the
question to that schema.

has_tools.py answers the same question with a hand-rolled TOOL_CALL: convention
and a regular expression.
"""

import datetime, json, urllib.request

BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
CHAT_ENDPOINT = BASE + "/chat/completions"
QUESTION = "What time is it now?"
SYSTEM = "Use English for the conversation."

def get_current_time():
    return datetime.datetime.now().strftime("%H:%M")

TOOL_SCHEMAS_CLEAR = [{
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Get the current time. Use it when the user asks what time it is.",
        "parameters": {"type": "object", "properties": {}},
    },
}]

TOOL_SCHEMAS_UNCLEAR_DESCRIPTION = [{
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "X@?A",
        "parameters": {"type": "object", "properties": {}},
    },
}]

TOOL_SCHEMAS_UNCLEAR_NAME = [{
    "type": "function",
    "function": {
        "name": "XXX",
        "description": "Get the current time. Use it when the user asks what time it is.",
        "parameters": {"type": "object", "properties": {}},
    },
}]

TOOL_SCHEMAS_UNCLEAR_NAME_DESCRIPTION = [{
    "type": "function",
    "function": {
        "name": "XXX",
        "description": "Y@?A",
        "parameters": {"type": "object", "properties": {}},
    },
}]

# Compare how much the model leans on a legible name vs. a legible description
# to decide whether/what to call - each variant keeps everything else fixed.
VARIANTS = {
    "clear name + clear description": TOOL_SCHEMAS_CLEAR,
    "clear name + unclear description": TOOL_SCHEMAS_UNCLEAR_DESCRIPTION,
    "unclear name + clear description": TOOL_SCHEMAS_UNCLEAR_NAME,
    "unclear name + unclear description": TOOL_SCHEMAS_UNCLEAR_NAME_DESCRIPTION,
}

def chat(messages, tool_schemas):
    body = json.dumps({"model": MODEL, "temperature": 0, "reasoning_effort": "none",
                       "tools": tool_schemas,   # the schemas replace the prose tool rules
                       "messages": messages}).encode()
    req = urllib.request.Request(CHAT_ENDPOINT,
                                 data=body, headers=HEAD)
    with urllib.request.urlopen(req) as r:
        return json.load(r)["choices"][0]["message"]

def run_tool(tool_call, tools):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"] or "{}")   # arguments is a string, not a dict
    func = tools.get(name)
    if func is None:
        return f"Error: no tool named {name}"
    return func(**args)

def run_variant(label, tool_schemas):
    # the schema's own name is the only key the model ever sees, so the
    # lookup table has to key off it too, even when that name is nonsense
    tools = {tool_schemas[0]["function"]["name"]: get_current_time}

    print(f"\n=== {label} ===")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": QUESTION}]
    print(f"[User] {QUESTION}")

    msg = chat(messages, tool_schemas)
    tool_calls = msg["tool_calls"]
    if not tool_calls:
        print(f"[Assistant] {msg['content'].strip()}")
        return
    requested = ", ".join(f"{c['function']['name']}({c['function']['arguments'] or '{}'})"
                          for c in tool_calls)
    print(f"[Assistant] [tool_calls] {requested}")

    messages.append(msg)   # the assistant message goes back verbatim, tool_calls and all
    for tool_call in tool_calls:
        result = run_tool(tool_call, tools)
        print(f"[Tool] {tool_call['function']['name']} returned {result}")
        messages.append({"role": "tool",
                         "tool_call_id": tool_call["id"],   # ties the result back to which call it answers
                         "content": result})

    print(f"[Assistant] {chat(messages, tool_schemas)['content'].strip()}")

for label, tool_schemas in VARIANTS.items():
    run_variant(label, tool_schemas)
