import asyncio
from db import Session,engine
from models import Stock,SchemaState,Account,Item
async def main():
    async with Session() as s:
        async with s.begin():
            if await s.get(SchemaState,1) is None:s.add(SchemaState(id=1,version=2))
            for tenant,user in [('school-a','alice'),('school-b','bob')]:
                if await s.get(Stock,tenant) is None:s.add(Stock(tenant=tenant,available=100))
                if await s.get(Account,tenant) is None:s.add(Account(tenant=tenant,balance=0))
                if await s.get(Item,(tenant,1)) is None:s.add(Item(tenant=tenant,id=1,owner=user,name='Seed '+tenant))
    await engine.dispose()
if __name__=='__main__':asyncio.run(main())
