from ...base_schema import AuthModel

class DeleteTodoModel(AuthModel):

    username: str 
    workspace_default_name: str
    todolist_id: int
    todo_id: int
    
    def get_auth_user(self) -> str:
        return self.username
    
    class Config:
        orm_mode = True