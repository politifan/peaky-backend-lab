from fastapi import FastAPI
from pydantic import BaseModel,ConfigDict,Field,field_validator
app=FastAPI()
class Preview(BaseModel):
 model_config=ConfigDict(extra='forbid')
 title:str=Field(min_length=1,max_length=80)
 priority:int=Field(default=1,ge=0,le=3,strict=True)
 @field_validator('title')
 @classmethod
 def title_clean(cls,v):
  v=v.strip()
  if not v:raise ValueError('empty')
  return v
@app.post('/preview')
def preview(data:Preview):return data
