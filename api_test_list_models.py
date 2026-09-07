import json, urllib.request

# OpenAI API
with urllib.request.urlopen("http://localhost:1234/v1/models") as r:
    for m in json.load(r)["data"]:
        print(m["id"])

# LM Studio API
with urllib.request.urlopen("http://localhost:1234/api/v1/models") as r:
    for m in json.load(r)["models"]:
        print(m["key"])