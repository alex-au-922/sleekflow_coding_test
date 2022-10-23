from ...base_schema import AuthModel

class InviteWorkspaceModel(AuthModel):
    """Create workspace model class for api"""

    owner_username: str
    workspace_default_name: str
    invitee_username: str

    def get_auth_user(self) -> str:
        """Get auth user"""
        return self.owner_username

    class Config:
        """Pydantic config class"""
        orm_mode = True