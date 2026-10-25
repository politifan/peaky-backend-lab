watermark, lateness = 10, 2
times = [7, 8, 12]
print([t for t in times if t >= watermark - lateness])
