from .db import ImageSearchSystem
from app.core.settings import settings

elastic = ImageSearchSystem(
    settings.database_url,
    settings.database_index,
)
