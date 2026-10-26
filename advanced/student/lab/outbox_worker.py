"""Durable queue protocol; send to a declared local demo endpoint."""
import asyncio,json,os,time
import httpx
from sqlalchemy import select,update
from db import Session,engine
from models import Outbox
from delivery_signature import signature
from mock_receiver import TRAINING_SECRET
async def claim(now,ttl=10):
    async with Session() as s:
        async with s.begin():
            r=(await s.execute(select(Outbox).where(Outbox.state=='pending',Outbox.due<=now,Outbox.lease_until<=now).order_by(Outbox.due,Outbox.id).with_for_update(skip_locked=True).limit(1))).scalar_one_or_none()
            if r is None:return None
            r.token+=1;r.lease_until=now+ttl
            return {'id':r.id,'event':r.event,'tenant':r.tenant,'payload':r.payload,'token':r.token}
async def settle(job,success,now):
    async with Session() as s:
        async with s.begin():
            stmt=update(Outbox).where(Outbox.id==job['id'],Outbox.token==job['token'],Outbox.state=='pending')
            if success:stmt=stmt.values(state='sent',lease_until=0)
            else:stmt=stmt.values(due=now+5,lease_until=0)
            changed=(await s.execute(stmt)).rowcount
    return changed==1
async def main():
    url=os.environ.get('DELIVERY_URL','http://127.0.0.1:8001/mock/events')
    if url not in {'http://127.0.0.1:8001/mock/events','http://receiver:8001/mock/events'}:raise ValueError('Local demo endpoint only')
    async with httpx.AsyncClient(timeout=httpx.Timeout(3,connect=1,pool=1)) as client:
        for _ in range(10):
            job=await claim(int(time.time()))
            if job is None:break
            try:
                body=json.dumps({'event':job['event'],'tenant':job['tenant'],'payload':json.loads(job['payload'])},sort_keys=True,separators=(',',':')).encode()
                stamp=str(int(time.time()));secret=os.environ.get('DELIVERY_SECRET',TRAINING_SECRET)
                response=await client.post(url,content=body,headers={'Content-Type':'application/json','X-Lantern-Timestamp':stamp,'X-Lantern-Signature':signature(secret,stamp,body)})
                success=200<=response.status_code<300
            except httpx.HTTPError:success=False
            await settle(job,success,int(time.time()))
    await engine.dispose()
if __name__=='__main__':asyncio.run(main())
