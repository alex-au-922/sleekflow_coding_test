from sqlalchemy.exc import NoResultFound # type: ignore
from sqlalchemy.orm import Session # type: ignore
from util.exceptions import NotFoundError
from .models import Account, Login, Todo, TodoList, WorkSpace, WorkSpaceAccountLink

class QueryWrapper:

    def __init__(self, session: Session) -> None:
        self.session = session

    def check_user_exists_and_get(self, username: str) -> Account:
        """Check if a user exists."""
        try:
            
            user: Account = self.session.query(Account).filter(Account.username == username).one()
            return user
        except NoResultFound:
            raise NotFoundError(f'User "{username}" not found.')

    def check_workspace_exists_and_get(self, workspace_default_name: str) -> WorkSpace:
        """Check if a user exists."""
        try:
            workspace: WorkSpace = self.session.query(WorkSpace).filter(WorkSpace.workspace_default_name == workspace_default_name).one()
            return workspace
        except NoResultFound:
            raise NotFoundError(f'Workspace "{workspace_default_name}" not found.')

    def check_todolist_exists_and_get(self, todolist_id: int) -> TodoList:
        """Check if a user exists."""
        try:
            todolist: TodoList = self.session.query(TodoList).filter(TodoList.todolist_id == todolist_id).one()
            return todolist
        except NoResultFound:
            raise NotFoundError(f'Todo list of id "{todolist_id}" not found.')

    def check_todo_exists_and_get(self, todo_id: int) -> Todo:
        """Check if a user exists."""
        try:
            todo: Todo = self.session.query(Todo).filter(Todo.todo_id == todo_id).one()
            return todo
        except NoResultFound:
            raise NotFoundError(f'Todo of id "{todo_id}" not found.')

    def check_user_in_workspace_and_get(self, username: str, workspace_default_name: str) -> WorkSpaceAccountLink:
        """Check if a user exists."""
        try:
            user: Account = (
                self.session
                    .query(WorkSpaceAccountLink)
                    .join(Account, WorkSpaceAccountLink.user_id == Account.user_id)
                    .join(WorkSpace, WorkSpaceAccountLink.workspace_id == WorkSpace.workspace_id)
                    .filter(Account.username == username)
                    .filter(WorkSpace.workspace_default_name == workspace_default_name)
                    .one()
            )
            return user
        except NoResultFound:
            raise NotFoundError(f'User "{username}" has not joined workspace "{workspace_default_name}".')

    def check_user_logined_and_get(self,username: str) -> Login:
        """Check if a user exists."""
        try:
            user: Account = (
                self.session
                    .query(Account)
                    .join(Login, Login.user_id == Account.user_id)
                    .filter(Account.username == username)
                    .one()
            )
            return user
        except NoResultFound:
            raise NotFoundError(f'User "{username}" is not logined.')