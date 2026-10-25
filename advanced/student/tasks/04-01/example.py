import hashlib, json
body = {"amount": 100, "currency": "DEMO"}
canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
print(len(hashlib.sha256(canonical.encode()).hexdigest()))
