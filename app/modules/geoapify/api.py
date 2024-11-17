import traceback
import requests
from requests.structures import CaseInsensitiveDict
from app.core.settings import settings

from typing import TypedDict, List, Literal

class TimezoneDict(TypedDict):
    name: str
    offset_STD: str
    offset_STD_seconds: int
    offset_DST: str
    offset_DST_seconds: int
    abbreviation_STD: str
    abbreviation_DST: str

class DatasourceDict(TypedDict):
    sourcename: str
    attribution: str
    license: str
    url: str

class RankDict(TypedDict):
    importance: float
    popularity: float

class GeometryDict(TypedDict):
    type: Literal["Point"]
    coordinates: List[float]

class PropertiesDict(TypedDict):
    datasource: DatasourceDict
    name: str
    country: str
    country_code: str
    state: str
    county: str
    city: str
    postcode: str
    district: str
    suburb: str
    street: str
    housenumber: str
    lon: float
    lat: float
    state_code: str
    distance: int
    result_type: str
    formatted: str
    address_line1: str
    address_line2: str
    category: str
    timezone: TimezoneDict
    plus_code: str
    plus_code_short: str
    rank: RankDict
    place_id: str

def reverse_geocode(lat: float, lon: float):
    url = f"https://api.geoapify.com/v1/geocode/reverse?lat={lat}&lon={lon}&apiKey={settings.geoapify_api_key}"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    resp = requests.get(url, headers=headers)

    data = resp.json()

    try:
        return PropertiesDict(data['features'][0]['properties'])
    except (IndexError, KeyError):
        traceback.print_exc()
        return None
