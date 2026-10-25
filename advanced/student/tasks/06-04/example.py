seen = {"e-1"}
events = ["e-1", "e-2", "e-2"]
applied = []
for event in events:
    if event not in seen:
        seen.add(event)
        applied.append(event)
print(applied)
