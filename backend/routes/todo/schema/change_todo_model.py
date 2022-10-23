from ...base_schema import AuthModel
from datetime import datetime, date
from typing import Optional, Union

class ChangeTodoModel(AuthModel):

    username: str 
    workspace_default_name: str
    todolist_id: int
    todo_id: int
    todo_name: Optional[str] = None
    todo_description: Optional[str] = None
    todo_due_date: Optional[Union[datetime, date]] = None
    todo_status: Optional[str] = None
    todo_priority: Optional[str] = None
    
    def get_auth_user(self) -> str:
        return self.username
    
    def get_last_modified(self) -> datetime:
        return datetime.now()
    
    class Config:
        orm_mode = True