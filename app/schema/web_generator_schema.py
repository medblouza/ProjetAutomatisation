from typing import List
from pydantic import BaseModel


class WebFile(BaseModel):
    path: str
    content: str


class GeneratedSite(BaseModel):
    site_name: str
    files: List[WebFile]