"""Explicit persistence incident; never deletes or replaces a database."""
from pathlib import Path
import sys
mode=sys.argv[1] if len(sys.argv)>1 else 'none'
if mode not in ['none','lost_commit']:raise SystemExit('Use none or lost_commit')
path=Path(__file__).resolve().parent/'app/main.py';source=path.read_text(encoding='utf-8')
lines=source.splitlines(keepends=True);matches=[i for i,line in enumerate(lines) if '# PERSISTENCE' in line]
if len(matches)!=1:raise SystemExit('Expected one PERSISTENCE marker; preserve your own edited source')
index=matches[0]
if lines[index].strip() not in ['try:session.commit() # PERSISTENCE','try:session.flush() # PERSISTENCE']:raise SystemExit('Marker line contains your own change; choose the transaction explicitly')
indent=lines[index][:len(lines[index])-len(lines[index].lstrip())]
lines[index]=indent+'try:session.'+('commit' if mode=='none' else 'flush')+'() # PERSISTENCE\n'
path.write_text(''.join(lines),encoding='utf-8');print('Profile:',mode,'Restart your server; retain the same database.')
