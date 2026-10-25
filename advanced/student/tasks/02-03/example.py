balances = {"A": 100, "B": 0}
amount = 80
balances["A"] -= amount
balances["B"] += amount
print(sum(balances.values()))
