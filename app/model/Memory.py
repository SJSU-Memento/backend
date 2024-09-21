from datetime import datetime
from sqlmodel import Field, SQLModel

class Memory(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    description: str
    created_at: datetime = Field(default=datetime.utcnow)