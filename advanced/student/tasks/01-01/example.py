import asyncio
async def fetch(number, sem):
    async with sem:
        await asyncio.sleep(0.01)
        return number * 2
async def main():
    sem = asyncio.Semaphore(2)
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(fetch(i, sem)) for i in range(4)]
    print([t.result() for t in tasks])
asyncio.run(main())
