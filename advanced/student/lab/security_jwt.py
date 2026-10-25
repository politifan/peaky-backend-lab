"""Runnable JWT/password example. Demo identity adapter remains explicit in auth.py."""
import jwt
from pwdlib import PasswordHash
ALGORITHM='HS256'
ISSUER='lantern-demo'
AUDIENCE='lantern-api'
password_hasher=PasswordHash.recommended()
def hash_password(password):return password_hasher.hash(password)
def verify_password(password,hashed):return password_hasher.verify(password,hashed)
def issue(subject,scopes,now,ttl,secret):
    if not subject or ttl<=0:raise ValueError('subject and positive ttl required')
    return jwt.encode({'sub':subject,'scope':' '.join(sorted(set(scopes))),'iat':now,'exp':now+ttl,'iss':ISSUER,'aud':AUDIENCE},secret,algorithm=ALGORITHM)
def validate(token,secret):
    # Current time validation performed by PyJWT. Controlled-time tests use library
    # issued tokens around a fixed test clock at the adapter boundary.
    return jwt.decode(token,secret,algorithms=[ALGORITHM],issuer=ISSUER,audience=AUDIENCE,options={'require':['sub','iat','exp','iss','aud']})
