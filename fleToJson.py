import json
key_path = "serviceAccountKey.json"

with open(key_path) as f:
    data = json.load(f)
    print(json.dumps(data))  # This gives a single-line JSON string
