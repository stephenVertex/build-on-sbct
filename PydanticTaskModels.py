from typing import Dict, List, Any, Optional, Union, Tuple
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json


def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return custom_json_serializer(obj)
        except TypeError:
            return super().default(obj)

class BaseModelWithCustomJSON(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            timedelta: str,
            Enum: lambda v: v.value,
            tuple: list,
        }

    def json(self, **kwargs):
        return json.dumps(self.dict(), cls=CustomJSONEncoder, **kwargs)

# Pydantic models
class TodoCreate(BaseModelWithCustomJSON):
    content: str = Field(..., min_length=1, max_length=1000)

class TodoOut(BaseModelWithCustomJSON):
    id: str
    content: str
    createdAt: datetime
    updatedAt: datetime

# Simplified Pydantic models for OKR
class OKRCreate(BaseModelWithCustomJSON):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)

class OKROut(BaseModelWithCustomJSON):
    id: str
    title: str
    description: str
    createdAt: datetime
    updatedAt: datetime

class TaskCreate(BaseModelWithCustomJSON):
    name: str
    description: Optional[str] = None
    estimated_time_mins: Optional[int] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None

class TaskOut(BaseModelWithCustomJSON):
    id: str
    name: str
    description: Optional[str] = None
    estimated_time_mins: Optional[int] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    createdAt: datetime
    updatedAt: datetime
    
class NullModel(BaseModelWithCustomJSON):
    value: None = None
