from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.db import get_async_session
from app.model.Memory import Memory
from app.schema import MemoryQuery

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/")
async def read_memories(query: MemoryQuery = Depends(), session = Depends(get_async_session)):
    """Get all memories."""

    where_clause = [Memory.description.ilike(f"%{query.query}%")]
    if query.start_datetime:
        where_clause.append(Memory.created_at >= query.start_datetime)
    if query.end_datetime:
        where_clause.append(Memory.created_at <= query.end_datetime)


    stmt = select(Memory).where(*where_clause)
    memories = await session.exec(stmt)

    return {
        "memories": memories.scalars().all()
    }

