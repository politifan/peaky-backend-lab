import os
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
URL=os.environ.get('DATABASE_URL','postgresql+asyncpg://lantern:demo-only@localhost:55432/lantern')
engine=create_async_engine(URL,pool_pre_ping=True)
Session=async_sessionmaker(engine,expire_on_commit=False)
