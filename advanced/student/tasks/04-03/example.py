local = {"op-1": 100, "op-2": 50}
remote = {"op-1": 100}
print(sorted(set(local) - set(remote)))
