import asyncio
from alembic import context
from db import engine
from models import Base
def configure(conn):
    context.configure(connection=conn,target_metadata=Base.metadata)
    with context.begin_transaction():context.run_migrations()
async def online():
    async with engine.connect() as conn:await conn.run_sync(configure)
    await engine.dispose()
if context.is_offline_mode():
    from db import URL
    context.configure(url=URL,target_metadata=Base.metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()
else:asyncio.run(online())
