from datetime import datetime
from sqlmodel import Field, SQLModel
from decimal import Decimal


class Memory(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    description: str
    created_at: datetime = Field(default=datetime.utcnow)
    image_source: str #link to Google Cloud
    #coordinates
    long: Decimal = Field(default=0, max_digits=3, decimal_places=6)
    lat: Decimal = Field(default=0, max_digits=3, decimal_places=6)
    # address
    city: str = Field(default='')
    state: str = Field(default='')
    zip: str = Field(default='')
    country: str = Field(default='')
    address: str = Field(default='')
    # audio
    audio_source: str
    audio_transcript: str
    orc_result: str

class Tag(SQLModel, table=True):
    name: str = Field(primary_key=True)
    memory_id: int = Field(foreign_key="memory.id", primary_key=True)
