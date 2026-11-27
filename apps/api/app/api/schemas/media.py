import uuid
from datetime import datetime

from pydantic import BaseModel


class PostMediaResponse(BaseModel):
    id: uuid.UUID
    url: str
    content_type: str
    byte_size: int
    width: int
    height: int
    created_at: datetime
