from decimal import Decimal
from random import randint
import traceback
from fastapi import APIRouter, HTTPException
from openai import BaseModel
from datetime import datetime
import os
from typing import Optional
import base64

from app.modules.elasticsearch import elastic
from app.modules.geoapify.api import reverse_geocode
from app.modules.metadata_extraction import extract_metadata_from_image
from app.core.settings import settings

router = APIRouter(prefix='/upload')

# Configure upload directory
UPLOAD_DIR = settings.storage_path
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadMemoryRequest(BaseModel):
    image: str
    location: Optional[str] = None
    timestamp: Optional[str] = None
    

@router.post("/")
async def upload_memory(
    memory: UploadMemoryRequest,
):
    image = memory.image
    location = memory.location
    timestamp = memory.timestamp

    try:
        if "base64," in image:
            image_data = image.split("base64,")[1]
        else:
            image_data = image 
            
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)

        # Generate unique filename using timestamp
        if not timestamp:
            timestamp_obj = datetime.now()
        else:
            timestamp_obj = datetime.fromisoformat(timestamp)
        filename = f"image_{timestamp_obj.strftime('%Y-%m-%d_%H-%M-%S')}-{randint(0,10000)}.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)

        lat, long = map(Decimal, location.split(",")) if location else (None, None)
        
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        if lat and long:
            reverse_geocode_result = reverse_geocode(lat, long)
            geocode_model_kwargs = {
                "city": reverse_geocode_result.get('city', ''),
                "state": reverse_geocode_result.get('state', ''),
                "zip": reverse_geocode_result.get('postcode', ''),
                "country": reverse_geocode_result.get('country', ''),
                "address": reverse_geocode_result.get('formatted', '')
            } if reverse_geocode_result else {}
        else:
            geocode_model_kwargs = {}
            # hacky way to handle missing location data
            long = Decimal(0)
            lat = Decimal(0)

        metadata = extract_metadata_from_image(image_bytes)

        doc_id = elastic.ingest_image_metadata(
            image_path=filename,
            timestamp=timestamp_obj,
            llm_description=metadata.description,
            location_data={
                "latitude": lat,
                "longitude": long,
                **geocode_model_kwargs
            },
            ocr_text=metadata.ocr,
            # tags=["sunset", "beach", "palm trees", "miami"],
            # additional_metadata={}
        )

        return {
            "status": "success",
            "id": doc_id
        }
        
    except Exception as e:
        # Delete the file if it was created but database operation failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload memory: {str(e)}"
        )
