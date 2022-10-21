from pydantic import BaseModel

class LoginModel(BaseModel):
    """Create user model class for api"""

    input_field: str
    password: str
    
    class Config:
        """Pydantic config class"""
        orm_mode = True