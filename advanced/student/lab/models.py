from sqlalchemy import Integer,String,UniqueConstraint,CheckConstraint
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
class Base(DeclarativeBase):pass
class SchemaState(Base):
    __tablename__='schema_state'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    version:Mapped[int]=mapped_column(Integer)
class Stock(Base):
    __tablename__='stock'
    tenant:Mapped[str]=mapped_column(String(120),primary_key=True)
    available:Mapped[int]=mapped_column(Integer)
    __table_args__=(CheckConstraint('available >= 0',name='ck_stock_nonnegative'),)
class Reservation(Base):
    __tablename__='reservation'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    tenant:Mapped[str]=mapped_column(String(120))
    key:Mapped[str]=mapped_column(String(120))
    qty:Mapped[int]=mapped_column(Integer)
    __table_args__=(UniqueConstraint('tenant','key',name='uq_reservation_key'),CheckConstraint('qty > 0',name='ck_reservation_positive'))
class Item(Base):
    __tablename__='item'
    tenant:Mapped[str]=mapped_column(String(120),primary_key=True)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    owner:Mapped[str]=mapped_column(String(120))
    name:Mapped[str]=mapped_column(String(200))
class Resource(Base):
    __tablename__='resource'
    name:Mapped[str]=mapped_column(String(120),primary_key=True)
    token:Mapped[int]=mapped_column(Integer)
    value:Mapped[str]=mapped_column(String(200))
class Account(Base):
    __tablename__='account'
    tenant:Mapped[str]=mapped_column(String(120),primary_key=True)
    balance:Mapped[int]=mapped_column(Integer)
class Inbox(Base):
    __tablename__='inbox'
    event:Mapped[str]=mapped_column(String(120),primary_key=True)
    tenant:Mapped[str]=mapped_column(String(120))
    delta:Mapped[int]=mapped_column(Integer)
class Outbox(Base):
    __tablename__='outbox'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    tenant:Mapped[str]=mapped_column(String(120))
    event:Mapped[str]=mapped_column(String(120),unique=True)
    payload:Mapped[str]=mapped_column(String(500))
    state:Mapped[str]=mapped_column(String(20),default='pending')
    due:Mapped[int]=mapped_column(Integer,default=0)
    lease_until:Mapped[int]=mapped_column(Integer,default=0)
    token:Mapped[int]=mapped_column(Integer,default=0)
