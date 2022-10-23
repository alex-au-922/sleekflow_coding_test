from ...base_schema import AuthModel

class ChangeTodoListNameModel(AuthModel):
    """Create todolist model class for api"""

    username: str
    workspace_default_name: str
    todolist_id: int
    new_todolist_name: str
    
    def get_auth_user(self) -> str:
        """Get auth user"""
        return self.username

    class Config:
        """Pydantic config class"""
        orm_mode = True