from contextlib import asynccontextmanager
from fastapi import FastAPI,Depends,HTTPException,Response
from fastapi.responses import HTMLResponse,JSONResponse
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy import select,update
from sqlalchemy.exc import IntegrityError
import html,json
from db import Session,engine
from models import SchemaState,Stock,Reservation,Item,Resource,Account,Inbox,Outbox
from auth import identity,require
import faults

@asynccontextmanager
async def lifespan(app):
    app.state.cache={}
    yield
    await engine.dispose()
app=FastAPI(title='Lantern Lab Peaky Minds',lifespan=lifespan)
app.state.cache={}
@app.exception_handler(IntegrityError)
async def constraint_conflict(request,exc):
    # Do not expose SQL, credentials, or database internals to the caller.
    return JSONResponse(status_code=409,content={'detail':'Concurrent constraint conflict'})
class StrictInput(BaseModel):model_config=ConfigDict(extra='forbid')
class ReserveIn(StrictInput):
    key:str=Field(min_length=1,max_length=120)
    qty:int=Field(strict=True,gt=0,le=100)
class ItemIn(StrictInput):
    id:int=Field(strict=True,ge=0)
    name:str=Field(min_length=1,max_length=200)
class ItemPatch(StrictInput):
    name:str=Field(min_length=1,max_length=200)
class WriteIn(StrictInput):
    token:int=Field(strict=True,ge=0)
    value:str=Field(max_length=200)
class EventIn(StrictInput):
    event:str=Field(min_length=1,max_length=120)
    delta:int=Field(strict=True,ge=-1000,le=1000)

@app.get('/live')
async def live():return {'live':True}
@app.get('/ready')
async def ready():
    try:
        async with Session() as s:r=await s.get(SchemaState,1)
        if r is None or r.version<2:raise HTTPException(503,'Schema not ready')
        return {'ready':True,'schema':r.version}
    except HTTPException:raise
    except Exception:raise HTTPException(503,'Database unavailable')

@app.post('/reservations',status_code=201)
async def reserve(body:ReserveIn,response:Response,ctx=Depends(identity)):
    require(ctx,'write');await ready()
    tenant=ctx['tenant']
    try:
        async with Session() as s:
            async with s.begin():
                old=(await s.execute(select(Reservation).where(Reservation.tenant==tenant,Reservation.key==body.key))).scalar_one_or_none()
                if old:
                    if old.qty!=body.qty:raise HTTPException(409,'Key body conflict')
                    response.status_code=200
                    return {'id':old.id,'qty':old.qty,'tenant':old.tenant,'replayed':True}
                st=(await s.execute(update(Stock).where(Stock.tenant==tenant,Stock.available>=body.qty).values(available=Stock.available-body.qty).returning(Stock.available))).scalar_one_or_none()
                if st is None:
                    # A blocked conditional UPDATE may follow a concurrent same-key winner.
                    old=(await s.execute(select(Reservation).where(Reservation.tenant==tenant,Reservation.key==body.key))).scalar_one_or_none()
                    if old and old.qty==body.qty:
                        response.status_code=200
                        return {'id':old.id,'qty':old.qty,'tenant':old.tenant,'replayed':True}
                    raise HTTPException(409,'Insufficient stock')
                r=Reservation(tenant=tenant,key=body.key,qty=body.qty);s.add(r);await s.flush()
                s.add(Outbox(tenant=tenant,event=f'reservation:{r.id}',payload=json.dumps({'id':r.id,'qty':r.qty}),state='pending',due=0,lease_until=0,token=0))
                result={'id':r.id,'qty':r.qty,'tenant':r.tenant,'replayed':False}
            return result
    except IntegrityError:
        # Concurrent same-key transaction has won; old transaction rolled back stock.
        async with Session() as s:
            old=(await s.execute(select(Reservation).where(Reservation.tenant==tenant,Reservation.key==body.key))).scalar_one_or_none()
            if old and old.qty==body.qty:
                response.status_code=200
                return {'id':old.id,'qty':old.qty,'tenant':old.tenant,'replayed':True}
        raise HTTPException(409,'Key conflict')

@app.get('/reservations/{rid}')
async def read_reservation(rid:int,ctx=Depends(identity)):
    require(ctx,'read')
    async with Session() as s:r=(await s.execute(select(Reservation).where(Reservation.id==rid,Reservation.tenant==ctx['tenant']))).scalar_one_or_none()
    if r is None:raise HTTPException(404,'Not found')
    return {'id':r.id,'qty':r.qty,'tenant':r.tenant}
@app.post('/items',status_code=201)
async def create_item(body:ItemIn,ctx=Depends(identity)):
    require(ctx,'write')
    try:
        async with Session() as s:
            async with s.begin():s.add(Item(tenant=ctx['tenant'],id=body.id,owner=ctx['user'],name=body.name))
    except IntegrityError:raise HTTPException(409,'Item exists')
    return {'id':body.id,'tenant':ctx['tenant'],'name':body.name}
async def item_data(i,ctx):
    async with Session() as s:r=await s.get(Item,(ctx['tenant'],i))
    if r is None or not(ctx['admin'] or r.owner==ctx['user']):raise HTTPException(404,'Not found')
    return {'id':r.id,'tenant':r.tenant,'name':r.name,'owner':r.owner}
@app.get('/items/{i}')
async def get_item(i:int,ctx=Depends(identity)):
    require(ctx,'read');return await item_data(i,ctx)
@app.get('/cached/{i}')
async def cached(i:int,ctx=Depends(identity)):
    require(ctx,'read')
    # Always establish permission before cache lookup. Key must still partition data.
    actual=await item_data(i,ctx)
    key=faults.cache_key(ctx['tenant'],ctx['user'],i)
    if key not in app.state.cache:app.state.cache[key]=actual
    return app.state.cache[key]
@app.patch('/items/{i}')
async def patch_item(i:int,body:ItemPatch,ctx=Depends(identity)):
    require(ctx,'write');await item_data(i,ctx)
    async with Session() as s:
        async with s.begin():await s.execute(update(Item).where(Item.tenant==ctx['tenant'],Item.id==i).values(name=body.name))
    app.state.cache.clear()
    return await item_data(i,ctx)

@app.post('/worker/{name}')
async def worker_write(name:str,body:WriteIn,ctx=Depends(identity)):
    require(ctx,'write');resource_name=ctx['tenant']+':'+name
    async with Session() as s:
        async with s.begin():
            r=(await s.execute(select(Resource).where(Resource.name==resource_name).with_for_update())).scalar_one_or_none()
            if r is None:r=Resource(name=resource_name,token=body.token,value=body.value);s.add(r)
            elif not faults.accept_token(body.token,r.token):raise HTTPException(409,'Stale worker')
            else:r.token=body.token;r.value=body.value
    return {'token':body.token,'value':body.value}
@app.get('/worker/{name}')
async def worker_read(name:str,ctx=Depends(identity)):
    require(ctx,'read')
    async with Session() as s:r=await s.get(Resource,ctx['tenant']+':'+name)
    if r is None:raise HTTPException(404,'Not found')
    return {'token':r.token,'value':r.value}

@app.post('/events')
async def receive(body:EventIn,ctx=Depends(identity)):
    require(ctx,'write')
    # Serialize consumer decisions on the tenant account, including inbox creation.
    async with Session() as s:
        async with s.begin():
            a=(await s.execute(select(Account).where(Account.tenant==ctx['tenant']).with_for_update())).scalar_one()
            seen=await s.get(Inbox,body.event)
            if seen and (seen.tenant!=ctx['tenant'] or seen.delta!=body.delta):raise HTTPException(409,'Event contract conflict')
            if faults.should_apply(seen is not None):a.balance+=body.delta
            if seen is None:s.add(Inbox(event=body.event,tenant=ctx['tenant'],delta=body.delta))
            result={'balance':a.balance,'event':body.event,'tenant':ctx['tenant']}
    return result
@app.get('/balance')
async def balance(ctx=Depends(identity)):
    require(ctx,'read')
    async with Session() as s:a=await s.get(Account,ctx['tenant'])
    return {'balance':a.balance,'tenant':a.tenant}

@app.get('/',response_class=HTMLResponse)
async def dashboard():
    async with Session() as s:
        stocks=(await s.execute(select(Stock))).scalars().all()
        pending=(await s.execute(select(Outbox))).scalars().all()
    cards=''.join(f'<article><h2>{html.escape(r.tenant)}</h2><b>{r.available}</b><p>Доступных единиц</p></article>' for r in stocks)
    return '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Lantern Lab</title><style>body{font:18px system-ui;background:#f2f4f8;color:#172234;margin:50px}main{display:flex;gap:24px}article{background:white;padding:28px;border-radius:18px;min-width:220px}b{font-size:54px}a{color:#285fca}</style><h1>Lantern Lab</h1><p>Peaky Minds · вымышленные данные · учебный монитор</p><main>'+cards+'</main><p>Outbox строк: '+str(len(pending))+'</p><p><a href="/docs">Открыть интерактивный контракт API</a></p></html>'
