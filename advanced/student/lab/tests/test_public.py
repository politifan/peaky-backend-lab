import asyncio
import uuid
import httpx
from app import app
from db import engine
def test_live_and_reservation():
    async def run():
        h={'Authorization':'Bearer school-a-owner'}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',headers=h) as c:
            assert (await c.get('/live')).status_code==200
            assert (await c.get('/ready')).status_code==200
            key=uuid.uuid4().hex
            r=await c.post('/reservations',json={'key':key,'qty':1})
            assert r.status_code==201
            rid=r.json()['id']
            assert (await c.get('/reservations/'+str(rid))).json()['qty']==1
            repeated=await c.post('/reservations',json={'key':key,'qty':1})
            assert repeated.json()['id']==rid
            assert (await c.post('/reservations',json={'key':key,'qty':2})).status_code==409
            assert (await c.post('/reservations',json={'key':uuid.uuid4().hex,'qty':True})).status_code==422
        await engine.dispose()
    asyncio.run(run())
