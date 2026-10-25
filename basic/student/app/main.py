import os
from datetime import datetime,timedelta,timezone
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from fastapi import FastAPI,Depends,HTTPException,Header
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from pydantic import BaseModel,ConfigDict,Field,field_validator
from sqlalchemy import create_engine,select,ForeignKey,UniqueConstraint,CheckConstraint,String
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker
from sqlalchemy.exc import IntegrityError

class Base(DeclarativeBase):pass
class User(Base):
 __tablename__='users'
 id:Mapped[int]=mapped_column(primary_key=True)
 username:Mapped[str]=mapped_column(String(50),unique=True)
 password_hash:Mapped[str]=mapped_column(String(255))
class Ticket(Base):
 __tablename__='tickets'
 __table_args__=(UniqueConstraint('owner_id','request_key',name='uq_ticket_owner_key'),CheckConstraint('priority BETWEEN 0 AND 3',name='ck_ticket_priority'))
 id:Mapped[int]=mapped_column(primary_key=True)
 owner_id:Mapped[int]=mapped_column(ForeignKey('users.id'),index=True)
 title:Mapped[str]=mapped_column(String(80))
 priority:Mapped[int]=mapped_column(default=1)
 request_key:Mapped[str]=mapped_column(String(100))
 request_title:Mapped[str]=mapped_column(String(80))
 request_priority:Mapped[int]=mapped_column()

class Registration(BaseModel):
 model_config=ConfigDict(extra='forbid')
 username:str=Field(min_length=1,max_length=50)
 password:str=Field(min_length=8,max_length=128)
 @field_validator('username')
 @classmethod
 def clean(cls,v):
  v=v.strip()
  if not v:raise ValueError('empty username')
  return v
class UserOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int
 username:str
class TicketIn(BaseModel):
 model_config=ConfigDict(extra='forbid')
 title:str=Field(min_length=1,max_length=80)
 priority:int=Field(default=1,ge=0,le=3,strict=True)
 @field_validator('title')
 @classmethod
 def clean(cls,v):
  v=v.strip()
  if not v:raise ValueError('empty title')
  if len(v)>80:raise ValueError('title too long')
  return v
class TicketPatch(BaseModel):
 model_config=ConfigDict(extra='forbid')
 title:str|None=Field(default=None,min_length=1,max_length=80)
 priority:int|None=Field(default=None,ge=0,le=3,strict=True)
 @field_validator('title')
 @classmethod
 def clean(cls,v):
  if v is None:raise ValueError('null title is forbidden')
  v=v.strip()
  if not v:raise ValueError('empty title')
  return v
 @field_validator('priority')
 @classmethod
 def nonnull(cls,v):
  if v is None:raise ValueError('null priority is forbidden')
  return v
class TicketOut(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int
 title:str
 priority:int

def create_app(database_url,secret,create_schema=False):
 if len(secret)<32:raise ValueError('JWT secret requires 32 characters')
 engine=create_engine(database_url,connect_args={'check_same_thread':False} if database_url.startswith('sqlite') else {})
 if database_url.startswith('sqlite'):
  from sqlalchemy import event
  @event.listens_for(engine,'connect')
  def fk(connection,record):connection.execute('PRAGMA foreign_keys=ON')
 if create_schema:Base.metadata.create_all(engine)
 sessions=sessionmaker(engine,expire_on_commit=False)
 app=FastAPI(title='Peaky Minds Ticket Lab',version='2.0')
 app.state.engine=engine;app.state.sessions=sessions
 passwords=PasswordHash.recommended()
 oauth=OAuth2PasswordBearer(tokenUrl='token')
 def db():
  with sessions() as session:yield session
 def user(token:str=Depends(oauth),session=Depends(db)):
  try:
   payload=jwt.decode(token,secret,algorithms=['HS256'],options={'require':['sub','exp']})
   uid=int(payload['sub'])
  except (InvalidTokenError,ValueError,TypeError,KeyError):raise HTTPException(401,'invalid token',headers={'WWW-Authenticate':'Bearer'})
  value=session.get(User,uid)
  if value is None:raise HTTPException(401,'invalid user')
  return value
 def accessible(session,uid,tid):
  value=session.scalar(select(Ticket).where(Ticket.id==tid,Ticket.owner_id==uid))
  if value is None:raise HTTPException(404,'ticket not found')
  return value
 @app.get('/health')
 def health():return {'ok':True}
 @app.get('/ready')
 def ready(session=Depends(db)):
  from sqlalchemy import text
  try:session.execute(text('SELECT id,priority FROM tickets LIMIT 1'))
  except Exception:raise HTTPException(503,'schema not ready')
  return {'ready':True}
 @app.post('/users',response_model=UserOut,status_code=201)
 def register(data:Registration,session=Depends(db)):
  value=User(username=data.username,password_hash=passwords.hash(data.password))
  session.add(value)
  try:session.commit()
  except IntegrityError:session.rollback();raise HTTPException(409,'username already exists')
  return value
 @app.post('/token')
 def token(form:OAuth2PasswordRequestForm=Depends(),session=Depends(db)):
  value=session.scalar(select(User).where(User.username==form.username))
  if value is None or not passwords.verify(form.password,value.password_hash):raise HTTPException(401,'invalid credentials')
  now=datetime.now(timezone.utc)
  return {'access_token':jwt.encode({'sub':str(value.id),'exp':now+timedelta(minutes=30)},secret,algorithm='HS256'),'token_type':'bearer'}
 @app.post('/tickets',response_model=TicketOut,status_code=201)
 def create(data:TicketIn,current=Depends(user),session=Depends(db),request_key:str=Header(alias='Idempotency-Key',min_length=1,max_length=100)):
  if not request_key.strip():raise HTTPException(422,'empty request key')
  existing=session.scalar(select(Ticket).where(Ticket.owner_id==current.id,Ticket.request_key==request_key))
  if existing:
   if existing.request_title!=data.title or existing.request_priority!=data.priority:raise HTTPException(409,'key conflicts with payload')
   return existing
  value=Ticket(owner_id=current.id,title=data.title,priority=data.priority,request_key=request_key,request_title=data.title,request_priority=data.priority)
  session.add(value)
  try:session.flush() # PERSISTENCE
  except IntegrityError:
   session.rollback()
   existing=session.scalar(select(Ticket).where(Ticket.owner_id==current.id,Ticket.request_key==request_key))
   if existing and existing.request_title==data.title and existing.request_priority==data.priority:return existing
   raise HTTPException(409,'key conflicts with payload')
  return value
 @app.get('/tickets',response_model=list[TicketOut])
 def listing(offset:int=0,limit:int=20,current=Depends(user),session=Depends(db)):
  if not 0<=offset or not 1<=limit<=100:raise HTTPException(422,'invalid page')
  return session.scalars(select(Ticket).where(Ticket.owner_id==current.id).order_by(Ticket.id).offset(offset).limit(limit)).all()
 @app.get('/tickets/{tid}',response_model=TicketOut)
 def read(tid:int,current=Depends(user),session=Depends(db)):return accessible(session,current.id,tid)
 @app.patch('/tickets/{tid}',response_model=TicketOut)
 def patch(tid:int,data:TicketPatch,current=Depends(user),session=Depends(db)):
  value=accessible(session,current.id,tid)
  for name,v in data.model_dump(exclude_unset=True).items():setattr(value,name,v)
  session.commit()
  return value
 @app.delete('/tickets/{tid}',status_code=204)
 def delete(tid:int,current=Depends(user),session=Depends(db)):
  value=accessible(session,current.id,tid);session.delete(value);session.commit()
  return None
 return app

if os.getenv('DATABASE_URL'):
 app=create_app(os.environ['DATABASE_URL'],os.environ['JWT_SECRET'])
