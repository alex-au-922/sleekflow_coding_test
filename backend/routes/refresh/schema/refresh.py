from pydantic import BaseModel

class RefreshModel(BaseModel):
    """Create user model class for api"""

    username: str
    refresh_token: str
    
    class Config:
        """Pydantic config class"""
        orm_mode = True