from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MemoryQuery(BaseModel):
    query: str
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None