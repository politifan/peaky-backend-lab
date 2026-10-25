"""Offline demo identity. Production JWT dependency is a separate student task."""
from fastapi import Header,HTTPException
DEMO_TOKENS={
 'school-a-owner':('school-a','alice',False,{'read','write'}),
 'school-a-admin':('school-a','admin',True,{'read','write'}),
 'school-a-reader':('school-a','reader',False,{'read'}),
 'school-b-owner':('school-b','bob',False,{'read','write'}),
 'school-b-admin':('school-b','admin',True,{'read','write'})}
async def identity(authorization:str=Header(default='')):
    token=authorization.removeprefix('Bearer ')
    if token not in DEMO_TOKENS:raise HTTPException(401,'Unknown demo identity')
    tenant,user,admin,scopes=DEMO_TOKENS[token]
    return {'tenant':tenant,'user':user,'admin':admin,'scopes':scopes}
def require(ctx,scope):
    if scope not in ctx['scopes']:raise HTTPException(403,'Scope required')
