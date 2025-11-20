# src/schemas/news.py
from pydantic import BaseModel
from typing import Optional
import importlib

# detect pydantic major version
_pydantic_spec = importlib.util.find_spec("pydantic")
try:
    import pydantic as _pydantic
    _PYDANTIC_VERSION = tuple(int(x) for x in _pydantic.__version__.split("."))
except Exception:
    _PYDANTIC_VERSION = (0,)

class PromptRequest(BaseModel):
    prompt: str

class NewsSummaryRequestSchema(BaseModel):
    content: str

class NewsOut(BaseModel):
    id: int
    url: str
    title: str
    time: str
    content: str
    summary: Optional[str]
    reason: Optional[str]
    upvotes: int
    is_upvoted: bool = False

    class Config:
        # Use pydantic v2 key if available, otherwise fallback to orm_mode for v1
        if _PYDANTIC_VERSION[0] >= 2:
            from_attributes = True
        else:
            orm_mode = True
