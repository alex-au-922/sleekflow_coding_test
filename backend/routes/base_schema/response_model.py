from typing import Any, Dict, Optional
from pydantic import BaseModel
from util.types import Serializable

class ResponseModel(BaseModel):
    """Response model class for api"""
    msg: Optional[str] = None
    data: Optional[Dict[str, Serializable]] = None
    error: Optional[str] = None
    error_msg: Optional[str] = None