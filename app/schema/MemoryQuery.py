from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MemoryQuery(BaseModel):
    query: str
    long: Optional[float] = None
    lat: Optional[float] = None
    radius: Optional[float] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None