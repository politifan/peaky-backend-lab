"""Two explicit teaching modes; JWT is integrated with the actual routes."""
import os
from fastapi import Header,HTTPException
DEMO_TOKENS={
 'school-a-owner':('school-a','alice',False,{'read','write'}),
 'school-a-admin':('school-a','admin',True,{'read','write'}),
 'school-a-reader':('school-a','reader',False,{'read'}),
 'school-b-owner':('school-b','bob',False,{'read','write'}),
 'school-b-admin':('school-b','admin',True,{'read','write'})}
async def identity(authorization:str=Header(default='')):
    mode=os.environ.get('AUTH_MODE','demo')
    if mode=='jwt':
        from jwt.exceptions import InvalidTokenError
        from security_jwt import validate
        secret=os.environ.get('JWT_SECRET','')
        if len(secret)<32:raise HTTPException(503,'JWT mode requires a configured secret')
        if not authorization.startswith('Bearer '):raise HTTPException(401,'Bearer token required',headers={'WWW-Authenticate':'Bearer'})
        try:
            claims=validate(authorization[7:],secret)
            if not isinstance(claims['sub'],str) or not claims['sub'] or not isinstance(claims['tenant'],str) or not claims['tenant'] or type(claims['admin']) is not bool or not isinstance(claims['scope'],str):raise ValueError('Invalid identity claims')
        except (InvalidTokenError,KeyError,TypeError,ValueError):raise HTTPException(401,'Invalid JWT',headers={'WWW-Authenticate':'Bearer'})
        return dict(tenant=claims['tenant'],user=claims['sub'],admin=claims['admin'],scopes=set(claims['scope'].split()))
    if mode!='demo':raise HTTPException(503,'Unknown authentication mode')
    token=authorization.removeprefix('Bearer ')
    if token not in DEMO_TOKENS:raise HTTPException(401,'Unknown demo identity')
    tenant,user,admin,scopes=DEMO_TOKENS[token]
    return {'tenant':tenant,'user':user,'admin':admin,'scopes':scopes}
def require(ctx,scope):
    if scope not in ctx['scopes']:raise HTTPException(403,'Scope required')
