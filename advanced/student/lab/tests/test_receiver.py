import json,sqlite3,time,subprocess,sys
from pathlib import Path
from fastapi.testclient import TestClient
from mock_receiver import create_app,TRAINING_SECRET
from delivery_signature import signature
def send(client,body,stamp=None,secret=TRAINING_SECRET):
    raw=json.dumps(body,sort_keys=True,separators=(',',':')).encode();stamp=str(int(time.time()) if stamp is None else stamp)
    return client.post('/mock/events',content=raw,headers={'Content-Type':'application/json','X-Lantern-Timestamp':stamp,'X-Lantern-Signature':signature(secret,stamp,raw)})
def test_signed_delivery_conflicts_and_restart(tmp_path):
    path=tmp_path/'receiver.sqlite';event=dict(event='r:1',tenant='school-a',payload={'qty':1})
    with TestClient(create_app(path,TRAINING_SECRET)) as client:
        assert client.post('/mock/events',json=event).status_code==401
        assert send(client,event,stamp=int(time.time())-600).status_code==401
        assert send(client,event,secret='another-training-secret-at-least-32-chars').status_code==401
        assert send(client,event).status_code==201
        assert send(client,event).json()['replayed'] is True
        assert send(client,dict(event,payload={'qty':2})).status_code==409
        assert send(client,dict(event,tenant='school-b')).status_code==201
    # A genuinely new interpreter observes the same persisted inbox, not globals.
    script="""import sys,json,time
from fastapi.testclient import TestClient
from mock_receiver import create_app,TRAINING_SECRET
from delivery_signature import signature
body=b'{"event":"r:1","tenant":"school-a","payload":{"qty":1}}';stamp=str(int(time.time()))
with TestClient(create_app(sys.argv[1],TRAINING_SECRET)) as client:
 r=client.post('/mock/events',content=body,headers={'X-Lantern-Timestamp':stamp,'X-Lantern-Signature':signature(TRAINING_SECRET,stamp,body)})
 assert r.status_code==200 and r.json()['replayed'] is True
print('restart replay confirmed')
"""
    result=subprocess.run([sys.executable,'-c',script,str(path)],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    with sqlite3.connect(path) as con:assert con.execute('SELECT COUNT(*) FROM deliveries').fetchone()[0]==2
