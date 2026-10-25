apps = [("reader-v1", 1, 2), ("writer-v2", 2, 3)]
schema = 1
print([name for name, low, high in apps if not low <= schema <= high])
