from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.db import get_async_session
from app.model.Memory import Memory
from app.schema import MemoryQuery
from app.modules.elasticsearch import elastic

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/")
async def read_memories(query: MemoryQuery = Depends()):
    """Get all memories."""

    location_filters = None
    if query.long and query.lat and query.radius:
        location_filters = {
            "long": query.long,
            "lat": query.lat,
            "radius": query.radius
        }

    temporal_filters = None
    if query.start and query.end:
        temporal_filters = {
            "start": query.start,
            "end": query.end
        }

    hybrid_results = elastic.search_images(
        query=query.query,
        location_filters=location_filters,
        temporal_filters=temporal_filters,
        search_type="hybrid"
    )

    return {
        "memories": hybrid_results
    }


