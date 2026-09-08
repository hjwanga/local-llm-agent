"""Let the model write a Python file and then execute it, and watch it chain the tools.

1. User: Write fizzbuzz.py: print 1 to 15 ... After writing it, run it and show me the output.
2. Assistant: tool_calls: create_file({"path":"fizzbuzz.py"})
3. Tool: Created fizzbuzz.py
4. Assistant: tool_calls: write_file({"path":"fizzbuzz.py","text":"for i in range(1, 16): ..."})
5. Tool: Wrote 182 characters to fizzbuzz.py
6. Assistant: tool_calls: run_python({"path":"fizzbuzz.py"})
7. Tool: 1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz  (one per line)
8. Assistant: the file it wrote, and the fifteen lines it printed.

"""

import json, os, subprocess, sys, urllib.request

BASE  = "http://localhost:1234/v1"
MODEL = "qwen/qwen3.5-9b"
HEAD  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
CHAT_ENDPOINT = BASE + "/chat/completions"
QUESTION = ("Write fizzbuzz.py: print 1 to 15, but Fizz for multiples of 3, Buzz for multiples "
            "of 5, FizzBuzz for multiples of 15, and the number itself otherwise. "
            "After writing it, run it and show me the output.")

SYSTEM = "Use English for the conversation."
MAX_ITERATIONS = 10   # a clean run needs 4; the rest is headroom for a model that loops
SANDBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox")
RUN_TIMEOUT  = 10     # seconds before a runaway program written by the model is killed
OUTPUT_LIMIT = 2000   # characters kept per stream, so one noisy program cannot flood the context

def resolve(path):
    # TODO(M3): the path allowlist goes here - realpath() the join and refuse
    # anything that does not sit under SANDBOX, so "../.." cannot escape.
    return os.path.join(SANDBOX, path)

def clip(text):
    return text if len(text) <= OUTPUT_LIMIT else text[:OUTPUT_LIMIT] + "... (truncated)"

def list_dir(path="."):
    target = resolve(path)
    if not os.path.isdir(target):
        return f"Error: {path} is not a directory"
    names = sorted(os.listdir(target))
    return ", ".join(names) if names else "(empty)"

def create_file(path):
    target = resolve(path)
    if os.path.exists(target):
        return f"Error: {path} already exists"
    open(target, "x", encoding="utf-8").close()
    return f"Created {path}"

def write_file(path, text):
    target = resolve(path)
    if not os.path.isfile(target):   # refuses to create, so create_file has to run first
        return f"Error: {path} does not exist, create it first"
    with open(target, "w", encoding="utf-8") as f:
        f.write(text)
    return f"Wrote {len(text)} characters to {path}"

def read_file(path):
    target = resolve(path)
    if not os.path.isfile(target):
        return f"Error: {path} does not exist"
    with open(target, encoding="utf-8") as f:
        return f.read()

def run_python(path):
    target = resolve(path)
    if not os.path.isfile(target):   # nothing to run until write_file has put the code there
        return f"Error: {path} does not exist"
    try:
        done = subprocess.run([sys.executable, target], cwd=SANDBOX,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"Error: timed out after {RUN_TIMEOUT}s"
    out, err = clip(done.stdout), clip(done.stderr)
    if done.returncode != 0:
        return f"Error: exited with code {done.returncode}\n{err}"
    if not out.strip():
        # A silent success tells the model nothing, so hand it the warnings if there are any.
        return err if err.strip() else "(no output)"
    return out

TOOLS = {"list_dir": list_dir, "create_file": create_file, "write_file": write_file,
         "read_file": read_file, "run_python": run_python}

TOOL_SCHEMAS = [{
    "type": "function",
    "function": {
        "name": "list_dir",
        "description": "List the file names in a directory. Use \".\" for the working "
                       "directory. Call it first when you need to know whether a file exists.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string",
                                    "description": "Directory to list, \".\" for the working directory."}},
            "required": ["path"],
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "create_file",
        "description": "Create a new, empty file. It never overwrites: creating a file that "
                       "already exists fails. A file must exist before write_file can write to it.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File to create."}},
            "required": ["path"],
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Replace the contents of an existing file with the given text. It never "
                       "creates: writing to a file that does not exist fails, so call create_file first.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File to write to."},
                           "text": {"type": "string", "description": "Text to store in the file."}},
            "required": ["path", "text"],
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read back and return the whole contents of an existing file. "
                       "Reading a file that does not exist fails.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File to read."}},
            "required": ["path"],
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "run_python",
        "description": "Run an existing Python file and return what it printed.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Python file to run, e.g. \"fizzbuzz.py\"."}},
            "required": ["path"],
        },
    },
}]

def chat(messages):
    body = json.dumps({"model": MODEL, "temperature": 0,
                       "reasoning_effort": "none",   # knob 1: raise this first if the model will not chain the calls
                       "tools": TOOL_SCHEMAS,
                       "messages": messages}).encode()
    req = urllib.request.Request(CHAT_ENDPOINT,
                                 data=body, headers=HEAD)
    with urllib.request.urlopen(req) as r:
        return json.load(r)["choices"][0]["message"]

def run_tool(tool_call):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"] or "{}")   # arguments is a string, not a dict
    func = TOOLS.get(name)
    if func is None:
        return f"Error: no tool named {name}"
    try:
        return func(**args)
    except TypeError as e:   # the model invented an argument, or left a required one out
        return f"Error: bad arguments for {name}: {e}"

os.makedirs(SANDBOX, exist_ok=True)

messages = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": QUESTION}]
print(f"[User] {QUESTION}")

# Agent-loop
# One pass of the loop is one API call. The model decides how many it needs:
# it keeps asking for tools until it has enough to answer, and the round that
# comes back without tool_calls is the answer.
for round_no in range(1, MAX_ITERATIONS + 1):
    print(f"\n=== round {round_no} ===")
    # 1.Think
    msg = chat(messages)

    tool_calls = msg.get("tool_calls")
    # finished
    if not tool_calls:
        print(f"[Assistant] {msg['content'].strip()}")
        break

    requested = ", ".join(f"{c['function']['name']}({c['function']['arguments'] or '{}'})"
                          for c in tool_calls)
    print(f"[Assistant] [tool_calls] {requested}")

    messages.append(msg)   # the assistant message goes back verbatim, tool_calls and all
    for tool_call in tool_calls:
        # 2.Act
        result = run_tool(tool_call)
        print(f"[Tool] {tool_call['function']['name']} returned {result!r}")
        # 3.Observe
        messages.append({"role": "tool",
                         "tool_call_id": tool_call["id"],   # ties the result back to which call it answers
                         "content": result})
else:
    print(f"\nStopped after {MAX_ITERATIONS} rounds without a final answer - "
          f"read the trace above to see where it started going in circles.")
