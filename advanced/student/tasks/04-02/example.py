now = 10
rows = [{"id": 1, "due": 10, "lease": 9, "sent": False},
        {"id": 2, "due": 9, "lease": 12, "sent": False}]
print([r["id"] for r in rows
       if not r["sent"] and r["due"] <= now and r["lease"] <= now])
