"""One explicit incident profile. Normal operation is the default."""
from pathlib import Path
import os,json
def active():
    path=Path(os.environ.get('PEAKY_INCIDENT_FILE',Path(__file__).resolve().parent/'incident.json'))
    return json.loads(path.read_text(encoding='utf-8'))['case'] if path.exists() else 'none'
def accept_token(incoming, stored):
    return True if active()=='worker' else incoming>stored

def cache_key(tenant,user,item_id):
    return str(item_id) if active()=='cache' else json.dumps([tenant,user,item_id],separators=(',',':'))

def should_apply(already_seen):
    return True if active()=='duplicate' else not already_seen
