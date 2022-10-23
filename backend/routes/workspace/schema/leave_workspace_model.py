from ...base_schema import AuthModel

class LeaveWorkspaceModel(AuthModel):
    """Create workspace model class for api"""

    username: str
    workspace_default_name: str

    def get_auth_user(self) -> str:
        """Get auth user"""
        return self.username

    class Config:
        """Pydantic config class"""
        orm_mode = True