import json
key = json.dumps(["a:b", "u", "item-1", 2],
                 ensure_ascii=False, separators=(",", ":"))
print(key)
