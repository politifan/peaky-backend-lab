required = {"orders:write", "orders:read"}
granted = {"orders:read"}
print(sorted(required - granted))
