from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class WebSearchItem(BaseModel):
    title: str
    link: str
    snippet: str

class WebSearchResponse(BaseModel):
    results: List[WebSearchItem]
    query_info: Optional[Dict[str, Any]] = None
    total_results: Optional[int] = 0
    status: Optional[str] = "success"
    error: Optional[str] = None

class WebResults(BaseModel):
    results: Dict[str, Any]