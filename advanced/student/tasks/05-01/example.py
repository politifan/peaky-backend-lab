import math
samples = sorted([1, 2, 3, 4, 100])
rank = math.ceil(0.95 * len(samples))
print(samples[rank - 1])
