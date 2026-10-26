"""Local teaching issuer. No authentication server or production key management."""
import os,time,argparse
from security_jwt import issue
p=argparse.ArgumentParser();p.add_argument('--user',required=True);p.add_argument('--tenant',required=True);p.add_argument('--scopes',default='read');a=p.parse_args()
secret=os.environ.get('JWT_SECRET','')
if len(secret)<32:raise SystemExit('Set JWT_SECRET (at least 32 characters) for your isolated lab')
print(issue(a.user,a.scopes.split(),int(time.time()),1800,secret,tenant=a.tenant))
