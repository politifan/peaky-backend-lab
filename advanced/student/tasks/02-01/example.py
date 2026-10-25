import asyncio
from sqlalchemy import update
from db import Session, engine
from models import Stock, Reservation
async def main():
    async with Session() as session:
        async with session.begin():
            session.add(Stock(tenant="_isolated_example", available=3))
            await session.flush()
            stmt = (update(Stock)
                .where(Stock.tenant == "_isolated_example",
                       Stock.available >= 2)
                .values(available=Stock.available - 2)
                .returning(Stock.available))
            available = (await session.execute(stmt)).scalar_one()
            session.add(Reservation(tenant="_isolated_example",
                                    key="demo", qty=2))
            await session.flush()
            print(available)
            await session.rollback()  # Пример не оставляет данных
    await engine.dispose()
asyncio.run(main())
