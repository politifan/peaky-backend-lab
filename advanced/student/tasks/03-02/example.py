tenant = "school-a"
rows = [{"id": 1, "tenant": "school-b"},
        {"id": 2, "tenant": "school-a"}]
print([r["id"] for r in rows if r["tenant"] == tenant])
