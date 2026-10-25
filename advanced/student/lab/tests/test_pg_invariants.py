import asyncio,uuid
import httpx
from sqlalchemy import update,select,func
from db import Session,engine,URL
from models import Stock,Reservation
from app import app
def test_real_postgresql_race():
    # This is required in CI. A SQLite substitute must fail, not silently skip.
    assert URL.startswith('postgresql+asyncpg:'),'Real PostgreSQL required for row-lock and concurrency acceptance'
    async def run():
        tag=uuid.uuid4().hex
        async with Session() as s:
            async with s.begin():await s.execute(update(Stock).where(Stock.tenant=='school-a').values(available=7))
        gate=asyncio.Event()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',headers={'Authorization':'Bearer school-a-owner'}) as c:
            async def one(i):
                await gate.wait()
                return await c.post('/reservations',json={'key':tag+'-'+str(i),'qty':1})
            tasks=[asyncio.create_task(one(i)) for i in range(20)]
            gate.set();rs=await asyncio.gather(*tasks)
            assert sum(r.status_code==201 for r in rs)==7
            assert sum(r.status_code==409 for r in rs)==13
        async with Session() as s:
            assert (await s.get(Stock,'school-a')).available==0
            assert await s.scalar(select(func.count()).select_from(Reservation).where(Reservation.key.like(tag+'-%')))==7
        # Restore seed stock for other public smoke tests on this isolated database.
        async with Session() as s:
            async with s.begin():await s.execute(update(Stock).where(Stock.tenant=='school-a').values(available=100))
        await engine.dispose()
    asyncio.run(run())
