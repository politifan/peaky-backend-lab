replicas, pool, overflow = 6, 10, 5
available = 100 - 20
print(replicas * (pool + overflow) <= available)
