from pydantic import BaseModel, ConfigDict, StrictInt
class OrderPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qty: StrictInt | None = None
    note: str | None = None
p = OrderPatch(note=None)
print(p.model_dump(exclude_unset=True))
