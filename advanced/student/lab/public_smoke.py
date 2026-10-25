"""Bounded local useful-operation check; not the full incident acceptance suite."""
import os,uuid,json
from urllib.parse import urlsplit
import httpx
url=os.environ.get('BASE_URL','http://127.0.0.1:8000')
parts=urlsplit(url)
if parts.scheme!='http' or parts.hostname not in {'127.0.0.1','localhost'} or parts.username or parts.password or parts.path not in {'','/'} or parts.query or parts.fragment:
    raise ValueError('Use your loopback training API only')
with httpx.Client(base_url=url,headers={'Authorization':'Bearer school-a-owner'},timeout=5,follow_redirects=False) as c:
    live=c.get('/live');assert live.status_code==200 and live.json()=={'live':True}
    ready=c.get('/ready');assert ready.status_code==200 and ready.json()['ready'] is True
    key='public-'+uuid.uuid4().hex
    created=c.post('/reservations',json={'key':key,'qty':1});assert created.status_code==201, 'New local reservation not accepted'
    obj=created.json();assert type(obj['id']) is int and obj['qty']==1 and obj['tenant']=='school-a'
    path='/reservations/'+str(obj['id'])
    old=c.get(path);assert old.status_code==200 and old.json()=={k:obj[k] for k in ['id','qty','tenant']}
    repeated=c.post('/reservations',json={'key':key,'qty':1});assert repeated.status_code==200
    assert repeated.json()['id']==obj['id'] and repeated.json()['replayed'] is True
    conflict=c.post('/reservations',json={'key':key,'qty':2});assert conflict.status_code==409
    foreign=c.get(path,headers={'Authorization':'Bearer school-b-owner'});assert foreign.status_code==404
    assert c.get(path).json()==old.json()
print(json.dumps({'passed':True,'transport':'real local HTTP','reservation_id':obj['id'],'scope':'create/read/repeat/conflict/foreign-read; restart and incident adapters are separate'}))
