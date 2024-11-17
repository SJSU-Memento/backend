from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query

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

    temporal_filters = {}
    if query.start:
        temporal_filters["start"] = query.start
    if query.end:
        temporal_filters["end"] = query.end

    hybrid_results = elastic.search_images(
        query=query.query,
        location_filters=location_filters,
        temporal_filters=temporal_filters,
        search_type="hybrid"
    )

    return {
        "memories": hybrid_results
    }

       
# Custom dependency to preprocess the timestamp
def parse_timestamp(timestamp: str = Query(...)) -> datetime:
    # for some reason the timestamp is stored in a different format
    # inside eslasticsearch, so we need to normalize it

    try:
        # Replace space with '+', assuming the space indicates a timezone issue
        normalized_timestamp = timestamp.replace(' ', '+')
        return datetime.fromisoformat(normalized_timestamp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {e}")


@router.get("/timeline")
async def read_temporal_memory(
    direction: Literal["before", "after", "both"],
    timestamp: datetime = Depends(parse_timestamp),
    limit: int = 10
    ):
    """Get a memory by ID."""

    if direction == "both":
        elastic_results = []
        elastic_results.extend(elastic.get_image_sequence(
            timestamp=timestamp,
            direction="before",
            limit=limit,
            # inclusive=True
        ))
        elastic_results.extend(elastic.get_image_sequence(
            timestamp=timestamp,
            direction="after",
            limit=limit,
            inclusive=True
        ))
    else:
        elastic_results = elastic.get_image_sequence(
            timestamp=timestamp,
            direction=direction,
            limit=limit,
        )

    return {
        "memories": elastic_results
    }

