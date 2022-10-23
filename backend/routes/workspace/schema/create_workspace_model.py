from ...base_schema import AuthModel
from pydantic import validator

class CreateWorkspaceModel(AuthModel):
    """Create workspace model class for api"""

    username: str
    workspace_default_name: str

    @validator("workspace_default_name")
    def workspace_default_name_must_not_empty(cls, v: str) -> str:
        """Validate that workspace default name must not be empty"""
        if not v.strip():
            raise ValueError("Workspace default name cannot be empty!")
        return v
    
    def get_auth_user(self) -> str:
        """Get auth user"""
        return self.username

    class Config:
        """Pydantic config class"""
        orm_mode = True