import os,json,asyncio,uuid
import httpx,pytest
from app import app
from db import engine
@pytest.fixture
def profile(tmp_path,monkeypatch):
    path=tmp_path/'incident.json';path.write_text(json.dumps({'case':os.environ.get('PEAKY_TEST_FAULT','none')}),encoding='utf-8');monkeypatch.setenv('PEAKY_INCIDENT_FILE',str(path))
def test_stale_worker(profile):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',headers={'Authorization':'Bearer school-a-owner'}) as c:
            path='/worker/'+uuid.uuid4().hex
            assert (await c.post(path,json={'token':1,'value':'old'})).status_code==200
            assert (await c.post(path,json={'token':2,'value':'new'})).status_code==200
            assert (await c.post(path,json={'token':1,'value':'late-old'})).status_code==409
            assert (await c.get(path)).json()['value']=='new'
        await engine.dispose()
    asyncio.run(run())
def test_cache_isolation(profile):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as c:
            i=int(uuid.uuid4().hex[:7],16)
            for school in ['a','b']:
                h={'Authorization':'Bearer school-'+school+'-owner'}
                assert (await c.post('/items',headers=h,json={'id':i,'name':'item-'+school})).status_code==201
                assert (await c.get('/cached/'+str(i),headers=h)).json()['name']=='item-'+school
        await engine.dispose()
    asyncio.run(run())
def test_event_once(profile):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',headers={'Authorization':'Bearer school-a-owner'}) as c:
            before=(await c.get('/balance')).json()['balance'];body={'event':uuid.uuid4().hex,'delta':3}
            assert (await c.post('/events',json=body)).json()['balance']==before+3
            assert (await c.post('/events',json=body)).json()['balance']==before+3
        await engine.dispose()
    asyncio.run(run())
