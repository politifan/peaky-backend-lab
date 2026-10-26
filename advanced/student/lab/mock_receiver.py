"""Signed receiver with a durable inbox and one stored effect per intent."""
from contextlib import asynccontextmanager,closing
from pathlib import Path
import os,time,json,hashlib,sqlite3
from fastapi import FastAPI,Request,HTTPException,Response
from pydantic import BaseModel,ConfigDict,Field,ValidationError
from delivery_signature import valid
TRAINING_SECRET='lantern-training-delivery-secret-only-20261026'
class Event(BaseModel):
    model_config=ConfigDict(extra='forbid')
    event:str=Field(min_length=1,max_length=120)
    tenant:str=Field(min_length=1,max_length=120)
    payload:dict
def create_app(database,secret,clock=time.time):
    path=Path(database)
    if len(secret)<32:raise ValueError('Delivery secret requires 32 characters')
    @asynccontextmanager
    async def lifespan(app):
        path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(path,timeout=10)) as con:
            con.execute('CREATE TABLE IF NOT EXISTS deliveries(tenant TEXT NOT NULL,event TEXT NOT NULL,body_hash TEXT NOT NULL,payload TEXT NOT NULL, PRIMARY KEY(tenant,event))');con.commit()
        yield
    app=FastAPI(title='Lantern durable teaching receiver',lifespan=lifespan)
    @app.post('/mock/events')
    async def receive(request:Request,response:Response):
        raw=await request.body();stamp=request.headers.get('X-Lantern-Timestamp','');supplied=request.headers.get('X-Lantern-Signature','')
        if not valid(secret,stamp,raw,supplied,int(clock())):raise HTTPException(401,'Invalid or expired delivery signature')
        try:body=Event.model_validate_json(raw)
        except ValidationError:raise HTTPException(422,'Invalid event contract')
        canonical=json.dumps(body.model_dump(),sort_keys=True,ensure_ascii=False,separators=(',',':'));digest=hashlib.sha256(canonical.encode()).hexdigest()
        with closing(sqlite3.connect(path,timeout=10)) as con:
            con.execute('BEGIN IMMEDIATE')
            old=con.execute('SELECT body_hash FROM deliveries WHERE tenant=? AND event=?',(body.tenant,body.event)).fetchone()
            if old:
                if old[0]!=digest:raise HTTPException(409,'Event intent conflict')
                response.status_code=200;return {'accepted':body.event,'replayed':True}
            con.execute('INSERT INTO deliveries(tenant,event,body_hash,payload) VALUES (?,?,?,?)',(body.tenant,body.event,digest,json.dumps(body.payload,ensure_ascii=False)));con.commit()
        response.status_code=201;return {'accepted':body.event,'replayed':False}
    return app
app=create_app(os.environ.get('RECEIVER_DATABASE','receiver.sqlite'),os.environ.get('DELIVERY_SECRET',TRAINING_SECRET))
