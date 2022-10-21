from pydantic import BaseModel, validator, Field
from util.helper.string import is_email_format, random_string

class CreateUserModel(BaseModel):
    """Create user model class for api"""

    username: str
    email: str
    password: str
    password_salt: str = Field(default_factory=random_string)

    @validator("username")
    def username_must_not_empty(cls, v: str) -> str:
        """Validate that username must not be empty"""
        if not v.strip():
            raise ValueError("Username cannot be empty!")
        return v

    @validator("email")
    def email_must_contain_at_symbol(cls, v: str) -> str:
        """Validate that email must be valid"""
        if not is_email_format(v):
            raise ValueError(f'Email "{v}" is invalid!')
        return v
    
    @validator("password")
    def password_longer_than_8_characters(cls, v: str) -> str:
        """Validate that password must be longer than 8 characters"""
        if len(v) < 8:
            raise ValueError("Password too short!")
        return v
    
    class Config:
        """Pydantic config class"""
        orm_mode = True

class UpdatePasswordModel(BaseModel):
    """Update password model class for api"""

    username: str
    old_password: str
    new_password: str
    new_password_salt: str = Field(default_factory=random_string)

    @validator("new_password")
    def password_longer_than_8_characters(cls, v: str) -> str:
        """Validate that password must be longer than 8 characters"""
        if len(v) < 8:
            raise ValueError("Password too short!")
        return v

    class Config:
        """Pydantic config class"""
        orm_mode = True