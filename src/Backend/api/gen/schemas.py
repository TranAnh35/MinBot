from pydantic import BaseModel
from typing import Dict, Any

class WebResults(BaseModel):
    results: Dict[str, Any]