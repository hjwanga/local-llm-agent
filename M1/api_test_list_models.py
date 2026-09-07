"""List the models served by a local LM Studio instance.

The same server exposes two catalogues, and this script prints both:

1. The OpenAI-compatible endpoint /v1/models, whose entries are keyed by "id".
2. The LM Studio native endpoint /api/v1/models, whose entries are keyed by "key".

Use it as a smoke test: if either list prints, the server is reachable and the
MODEL name used by the other scripts can be copied from the output.
"""

import json, urllib.request

# OpenAI API
with urllib.request.urlopen("http://localhost:1234/v1/models") as r:
    for m in json.load(r)["data"]:
        print(m["id"])

# LM Studio API
with urllib.request.urlopen("http://localhost:1234/api/v1/models") as r:
    for m in json.load(r)["models"]:
        print(m["key"])