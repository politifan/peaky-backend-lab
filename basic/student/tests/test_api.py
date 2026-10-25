import os
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client(tmp_path):
 app=create_app('sqlite:///'+str(tmp_path/'open-tests.db').replace('\\','/'),'tutorial-only-secret-with-32-characters',create_schema=True)
 with TestClient(app) as value:yield value
 app.state.engine.dispose()

def access(client,name):
 r=client.post('/users',json={'username':name,'password':'TutorialPassword42'})
 assert r.status_code==201
 r=client.post('/token',data={'username':name,'password':'TutorialPassword42'})
 assert r.status_code==200
 return {'Authorization':'Bearer '+r.json()['access_token']}

def test_created_ticket_visible_to_new_request(client):
 auth=access(client,'anna')
 r=client.post('/tickets',json={'title':'Сеть','priority':0},headers=dict(auth,**{'Idempotency-Key':'open-test'}))
 assert r.status_code==201
 r=client.get('/tickets/'+str(r.json()['id']),headers=auth)
 assert r.status_code==200
 assert r.json()['title']=='Сеть'

def test_wrong_priority_rejected(client):
 auth=access(client,'anna')
 r=client.post('/tickets',json={'title':'Сеть','priority':True},headers=dict(auth,**{'Idempotency-Key':'open-test'}))
 assert r.status_code==422

def test_user_response_has_no_password_hash(client):
 r=client.post('/users',json={'username':'anna','password':'TutorialPassword42'})
 assert r.status_code==201
 assert set(r.json())=={'id','username'}

def test_anonymous_cannot_list(client):
 assert client.get('/tickets').status_code==401
