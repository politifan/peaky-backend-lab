"""Deliberately process-local demo receiver; durable inbox is a student task."""
from fastapi import FastAPI
from pydantic import BaseModel
app=FastAPI(title='Lantern mock receiver')
class Event(BaseModel):
    event:str
    payload:dict
@app.post('/mock/events')
async def receive(body:Event):return {'accepted':body.event}
