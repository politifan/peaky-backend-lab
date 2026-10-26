import asyncio,json,sys
from pathlib import Path
from db import Session,engine
from models import SchemaState
from sqlalchemy import text
async def main(mode):
    if mode=='migration':
        async with Session() as s:
            async with s.begin():
                r=await s.get(SchemaState,1)
                if r.version>=2:
                    await s.execute(text('ALTER TABLE stock RENAME COLUMN available TO legacy_available'))
                    r.version=1
    elif mode=='none':
        async with Session() as s:
            async with s.begin():
                columns=set((await s.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='stock'"))).scalars())
                if 'legacy_available' in columns and 'available' not in columns:await s.execute(text('ALTER TABLE stock RENAME COLUMN legacy_available TO available'))
                r=await s.get(SchemaState,1)
                if r:r.version=2
    elif mode not in ('worker','cache','duplicate'):raise SystemExit('Use none migration worker cache duplicate')
    Path(__file__).resolve().with_name('incident.json').write_text(json.dumps({'case':mode,'schema_marker_only':False}),encoding='utf-8')
    await engine.dispose()
if __name__=='__main__':asyncio.run(main(sys.argv[1]))
