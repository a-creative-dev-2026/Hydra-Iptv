from pydantic import BaseModel
from typing import List, Optional

class Channel(BaseModel):
    name: str
    url: str
    logo: Optional[str] = None
    group: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None

class SearchResult(BaseModel):
    query: str
    found: bool
    count: int
    links: List[str]
    channels: List[Channel] = []
