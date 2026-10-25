jobs = {"import": [], "calculate": ["import"], "export": ["calculate"]}
done = {"import"}
print([name for name, deps in jobs.items()
       if name not in done and set(deps) <= done])
