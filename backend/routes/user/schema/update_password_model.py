from pydantic import BaseModel, validator

class UpdatePasswordModel(BaseModel):
    """Update password model class for api"""

    username: str
    old_password: str
    new_password: str

    @validator("new_password")
    def password_longer_than_8_characters(cls, v: str) -> str:
        """Validate that password must be longer than 8 characters"""
        if len(v) < 8:
            raise ValueError("Password too short!")
        return v

    class Config:
        """Pydantic config class"""
        orm_mode = True