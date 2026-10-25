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
    elif mode not in ('worker','cache','duplicate'):raise SystemExit('Use migration worker cache duplicate')
    # The three faulty adapters are already present. Injection records the chosen case.
    Path('incident.json').write_text(json.dumps({'case':mode,'schema_marker_only':False}),encoding='utf-8')
    await engine.dispose()
if __name__=='__main__':asyncio.run(main(sys.argv[1]))
