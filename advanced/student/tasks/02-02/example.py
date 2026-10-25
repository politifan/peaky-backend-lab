rows = [(1, 12), (1, 10), (2, 2)]
after = (1, 10)
print([r for r in sorted(rows) if r > after])
