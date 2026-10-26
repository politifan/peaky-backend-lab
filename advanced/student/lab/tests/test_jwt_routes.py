import asyncio,time,uuid,os
import httpx,jwt
from security_jwt import issue,ISSUER,AUDIENCE
from app import app
from db import engine
def test_real_route_jwt_identity(monkeypatch):
    secret='local-jwt-route-training-key-20261026';monkeypatch.setenv('AUTH_MODE','jwt');monkeypatch.setenv('JWT_SECRET',secret)
    now=int(time.time());tag=uuid.uuid4().hex
    def token(user='alice',tenant='school-a',scopes=('read','write'),issued=now,ttl=120):return issue(user,scopes,issued,ttl,secret,tenant=tenant)
    def headers(value):return {'Authorization':'Bearer '+value}
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            path='/items/'+str(int(tag[:7],16));good=headers(token())
            assert (await client.get(path)).status_code==401
            assert (await client.get(path,headers=headers('school-a-owner'))).status_code==401
            assert (await client.get(path,headers=headers(token(issued=now-600,ttl=1)))).status_code==401
            forged=jwt.encode(dict(sub='alice',tenant='school-a',scope='read',admin=False,iat=now,exp=now+120,iss=ISSUER,aud='wrong-audience'),secret,algorithm='HS256')
            assert (await client.get(path,headers=headers(forged))).status_code==401
            assert (await client.post('/items',headers=headers(token(scopes=('read',))),json={'id':int(tag[:7],16),'name':'jwt '+tag})).status_code==403
            assert (await client.post('/items',headers=good,json={'id':int(tag[:7],16),'name':'jwt '+tag})).status_code==201
            assert (await client.get(path,headers=good)).json()['name']=='jwt '+tag
            assert (await client.get(path,headers=headers(token(user='bob',tenant='school-b')))).status_code==404
            assert (await client.patch(path,headers=headers(token(user='bob')),json={'name':'foreign'})).status_code==404
            assert (await client.get(path,headers=good)).json()['name']=='jwt '+tag
        await engine.dispose()
    asyncio.run(run())
